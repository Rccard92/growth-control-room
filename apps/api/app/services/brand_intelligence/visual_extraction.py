"""Extract visual identity proposal from public website HTML."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

from app.schemas.brand_identity_visual import (
    VisualColorSwatch,
    VisualExtractProposal,
    VisualExtractResponse,
    VisualFontEntry,
)
from app.services.brand_intelligence.source_fetcher import _http_get, _preclean_html

_HEX_RE = re.compile(r"#([0-9a-fA-F]{3,8})\b")
_RGB_RE = re.compile(
    r"rgb\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", re.I
)
_FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)


def _normalize_hex(hex_val: str) -> str:
    h = hex_val.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) >= 6:
        return f"#{h[:6].upper()}"
    return f"#{h.upper()}"


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def _luminance(hex_val: str) -> float:
    h = hex_val.lstrip("#")
    if len(h) != 6:
        return 0.5
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def _assign_roles(colors: list[tuple[str, int]]) -> list[VisualColorSwatch]:
    if not colors:
        return []
    sorted_colors = sorted(colors, key=lambda x: x[1], reverse=True)
    swatches: list[VisualColorSwatch] = []
    used_roles: set[str] = set()

    for hex_val, count in sorted_colors[:12]:
        lum = _luminance(hex_val)
        role: str | None = None
        if "primary" not in used_roles and len(swatches) == 0:
            role = "primary"
        elif "secondary" not in used_roles and len(swatches) == 1:
            role = "secondary"
        elif "accent" not in used_roles and 0.2 < lum < 0.85:
            role = "accent"
        elif "background" not in used_roles and lum > 0.85:
            role = "background"
        elif "text" not in used_roles and lum < 0.25:
            role = "text"
        confidence = min(0.9, 0.5 + count * 0.05)
        if role:
            used_roles.add(role)
        swatches.append(
            VisualColorSwatch(hex=hex_val, role=role, confidence=round(confidence, 2))
        )
    return swatches


class _VisualHTMLParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.og_image: str | None = None
        self.favicon: str | None = None
        self.meta_description: str | None = None
        self.header_images: list[str] = []
        self._in_header = False
        self._header_depth = 0
        self._style_chunks: list[str] = []
        self._inline_styles: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {k: (v or "") for k, v in attrs}
        if tag in ("header", "nav"):
            self._in_header = True
            self._header_depth += 1
        if tag == "meta":
            prop = (attr_map.get("property") or attr_map.get("name") or "").lower()
            content = attr_map.get("content", "").strip()
            if prop == "og:image" and content:
                self.og_image = urljoin(self.base_url, content)
            if prop == "description" and content:
                self.meta_description = content
        if tag == "link":
            rel = (attr_map.get("rel") or "").lower()
            href = attr_map.get("href", "").strip()
            if href and ("icon" in rel or "apple-touch-icon" in rel):
                self.favicon = urljoin(self.base_url, href)
        if tag == "img":
            src = attr_map.get("src", "").strip()
            if src:
                full = urljoin(self.base_url, src)
                if self._in_header and len(self.header_images) < 3:
                    self.header_images.append(full)
        if tag == "style":
            self._style_chunks.append("")
        style = attr_map.get("style", "")
        if style:
            self._inline_styles.append(style)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("header", "nav") and self._header_depth > 0:
            self._header_depth -= 1
            if self._header_depth == 0:
                self._in_header = False

    def handle_data(self, data: str) -> None:
        if self._style_chunks:
            self._style_chunks[-1] += data

    def all_css_text(self) -> str:
        return "\n".join(self._style_chunks + self._inline_styles)


def _extract_colors_from_css(css: str) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for match in _HEX_RE.finditer(css):
        hex_val = _normalize_hex(match.group(0))
        if len(hex_val) == 7:
            counts[hex_val] = counts.get(hex_val, 0) + 1
    for match in _RGB_RE.finditer(css):
        hex_val = _rgb_to_hex(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        counts[hex_val] = counts.get(hex_val, 0) + 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)


def _extract_fonts_from_css(css: str) -> list[VisualFontEntry]:
    fonts: list[VisualFontEntry] = []
    seen: set[str] = set()
    for match in _FONT_FAMILY_RE.finditer(css):
        raw = match.group(1).strip().strip('"').strip("'")
        name = raw.split(",")[0].strip().strip('"').strip("'")
        if name and name.lower() not in ("inherit", "initial", "sans-serif", "serif") and name not in seen:
            seen.add(name)
            role = "primary" if len(fonts) == 0 else "secondary" if len(fonts) == 1 else None
            fonts.append(VisualFontEntry(name=name, role=role))
        if len(fonts) >= 3:
            break
    return fonts


async def extract_visual_from_website(website_url: str) -> VisualExtractResponse:
    warnings: list[str] = []
    url = website_url.strip()
    if not url:
        return VisualExtractResponse(
            proposal=VisualExtractProposal(),
            warnings=["URL sito non valido."],
        )

    status_code, html, error = await _http_get(url)
    if error or not html:
        warnings.append(error or f"Impossibile recuperare il sito (HTTP {status_code}).")
        return VisualExtractResponse(proposal=VisualExtractProposal(), warnings=warnings)

    cleaned = _preclean_html(html)
    parser = _VisualHTMLParser(url)
    try:
        parser.feed(cleaned)
        parser.close()
    except Exception:
        warnings.append("Errore durante il parsing HTML.")

    primary_logo = parser.og_image or (parser.header_images[0] if parser.header_images else None)
    favicon = parser.favicon
    if not primary_logo:
        warnings.append("Logo non individuato automaticamente.")
    if not favicon:
        parsed = urlparse(url)
        favicon = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"

    css_text = parser.all_css_text()
    color_counts = _extract_colors_from_css(css_text)
    palette = _assign_roles(color_counts)
    if not palette:
        warnings.append("Nessun colore estratto dal sito.")

    fonts = _extract_fonts_from_css(css_text)
    style_notes = None
    if parser.meta_description:
        style_notes = f"Stile suggerito da meta description: {parser.meta_description[:300]}"

    return VisualExtractResponse(
        proposal=VisualExtractProposal(
            primary_logo_url=primary_logo,
            favicon_url=favicon,
            color_palette=palette,
            fonts=fonts,
            visual_style_notes=style_notes,
        ),
        warnings=warnings,
    )
