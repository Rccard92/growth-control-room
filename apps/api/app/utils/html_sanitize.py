"""Whitelist HTML sanitizer for editorial article bodyHtml."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from html import escape

_ALLOWED_TAGS = frozenset(
    {
        "h2",
        "h3",
        "h4",
        "p",
        "ul",
        "ol",
        "li",
        "strong",
        "em",
        "a",
        "blockquote",
        "div",
        "table",
        "thead",
        "tbody",
        "tfoot",
        "tr",
        "th",
        "td",
        "figure",
        "figcaption",
        "br",
        "hr",
        "img",
    }
)
# Tags that never have a closing counterpart and must not enter the open-tag stack.
_VOID_TAGS = frozenset({"br", "hr", "img"})
_ALLOWED_LINK_ATTRS = frozenset({"href", "title", "rel", "target"})
_ALLOWED_CELL_ATTRS = frozenset({"colspan", "rowspan", "scope"})
_ALLOWED_DIV_CLASSES = frozenset(
    {
        "gcr-article-body",
        "gcr-article-note",
        "gcr-product-tip",
        "gcr-article-cta",
    }
)
_STRIP_TAGS = frozenset({"script", "style", "iframe", "object", "embed"})
# Tags we keep the content of, rewritten to the closest allowed equivalent.
# h1 belongs to the page title, so an in-body h1 becomes a section heading.
_TAG_ALIASES = {"h1": "h2", "h5": "h4", "h6": "h4", "b": "strong", "i": "em"}
_MAX_CELL_SPAN = 20


@dataclass
class _OpenTag:
    """An element seen in the source, and whether we actually emitted it."""

    tag: str
    emitted: bool


@dataclass
class SanitizeResult:
    html: str
    warnings: list[str] = field(default_factory=list)


class _SanitizingHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._open: list[_OpenTag] = []
        self._dropped_div_classes: set[str] = set()
        self._dropped_tags: set[str] = set()

    # -- helpers -----------------------------------------------------------

    def _render_open_tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> str | None:
        """Return the opening tag to emit, or None if the element must be dropped."""
        if tag == "a":
            rendered = _render_anchor(attrs)
            if rendered is None:
                self._dropped_tags.add("a (href non valido)")
            return rendered
        if tag == "div":
            class_value = _extract_div_class(attrs)
            if not class_value:
                self._dropped_div_classes.update(_all_classes(attrs) or {"(senza classe)"})
                return None
            return f'<div class="{escape(class_value, quote=True)}">'
        if tag == "img":
            return _render_image(attrs)
        if tag in ("td", "th"):
            return f"<{tag}{_render_cell_attrs(attrs)}>"
        return f"<{tag}>"

    def _start(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = _TAG_ALIASES.get(tag, tag)
        if tag in _STRIP_TAGS or tag not in _ALLOWED_TAGS:
            if tag not in _STRIP_TAGS:
                self._dropped_tags.add(tag)
            # Known-but-unsupported elements still get a stack frame so their
            # closing tag cannot close an ancestor we did emit.
            if tag not in _VOID_TAGS and tag not in _STRIP_TAGS:
                self._open.append(_OpenTag(tag, emitted=False))
            return

        rendered = self._render_open_tag(tag, attrs)
        if tag in _VOID_TAGS:
            if rendered is not None:
                self._parts.append(rendered)
            return

        if rendered is None:
            self._open.append(_OpenTag(tag, emitted=False))
            return

        self._parts.append(rendered)
        self._open.append(_OpenTag(tag, emitted=True))

    # -- HTMLParser hooks --------------------------------------------------

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start(tag.lower(), attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in _VOID_TAGS:
            self._start(tag_lower, attrs)
            return
        self._start(tag_lower, attrs)
        self.handle_endtag(tag_lower)

    def handle_endtag(self, tag: str) -> None:
        tag_lower = _TAG_ALIASES.get(tag.lower(), tag.lower())
        if tag_lower in _VOID_TAGS:
            return
        # Ignore a closing tag with no matching open element: closing anything
        # else here would truncate an ancestor that is still legitimately open.
        if not any(frame.tag == tag_lower for frame in self._open):
            return
        while self._open:
            frame = self._open.pop()
            if frame.emitted:
                self._parts.append(f"</{frame.tag}>")
            if frame.tag == tag_lower:
                break

    def handle_data(self, data: str) -> None:
        if data:
            self._parts.append(escape(data))

    # -- output ------------------------------------------------------------

    def get_html(self) -> str:
        while self._open:
            frame = self._open.pop()
            if frame.emitted:
                self._parts.append(f"</{frame.tag}>")
        return "".join(self._parts)

    def get_warnings(self) -> list[str]:
        warnings: list[str] = []
        if self._dropped_div_classes:
            classes = ", ".join(sorted(self._dropped_div_classes))
            warnings.append(
                "Div rimossi perché la classe non è tra quelle consentite "
                f"({classes}). Classi ammesse: {', '.join(sorted(_ALLOWED_DIV_CLASSES))}."
            )
        if self._dropped_tags:
            tags = ", ".join(sorted(self._dropped_tags))
            warnings.append(f"Tag HTML non consentiti rimossi dall'articolo: {tags}.")
        return warnings


def _all_classes(attrs: list[tuple[str, str | None]]) -> set[str]:
    for name, value in attrs:
        if name.lower() == "class" and value:
            return {cls.strip().lower() for cls in value.split() if cls.strip()}
    return set()


def _extract_div_class(attrs: list[tuple[str, str | None]]) -> str | None:
    for cls in sorted(_all_classes(attrs)):
        if cls in _ALLOWED_DIV_CLASSES:
            return cls
    return None


def _render_anchor(attrs: list[tuple[str, str | None]]) -> str | None:
    safe: dict[str, str] = {}
    for name, value in attrs:
        key = name.lower()
        if key not in _ALLOWED_LINK_ATTRS or value is None:
            continue
        if key == "href" and not _is_safe_href(value):
            continue
        if key == "target" and value.strip().lower() != "_blank":
            continue
        safe[key] = value
    if not safe.get("href"):
        # An anchor with no usable destination is noise: keep the text, drop the tag.
        return None
    if safe.get("target") == "_blank":
        # Never hand a new tab window.opener access to the article page.
        rel_parts = {part.lower() for part in safe.get("rel", "").split() if part}
        rel_parts.update({"noopener", "noreferrer"})
        safe["rel"] = " ".join(sorted(rel_parts))
    attr_str = "".join(f' {k}="{escape(v, quote=True)}"' for k, v in safe.items())
    return f"<a{attr_str}>"


def _render_image(attrs: list[tuple[str, str | None]]) -> str | None:
    src: str | None = None
    alt = ""
    for name, value in attrs:
        key = name.lower()
        if value is None:
            continue
        if key == "src" and _is_safe_href(value):
            src = value.strip()
        elif key == "alt":
            alt = value
    if not src:
        return None
    return f'<img src="{escape(src, quote=True)}" alt="{escape(alt, quote=True)}" loading="lazy">'


def _render_cell_attrs(attrs: list[tuple[str, str | None]]) -> str:
    safe: list[tuple[str, str]] = []
    for name, value in attrs:
        key = name.lower()
        if key not in _ALLOWED_CELL_ATTRS or value is None:
            continue
        if key in ("colspan", "rowspan"):
            try:
                span = int(str(value).strip())
            except ValueError:
                continue
            if not 1 <= span <= _MAX_CELL_SPAN:
                continue
            safe.append((key, str(span)))
        elif value.strip().lower() in ("row", "col", "rowgroup", "colgroup"):
            safe.append((key, value.strip().lower()))
    return "".join(f' {k}="{escape(v, quote=True)}"' for k, v in safe)


def _is_safe_href(href: str) -> bool:
    href = href.strip()
    if not href:
        return False
    lower = href.lower()
    if lower.startswith(("javascript:", "data:", "vbscript:")):
        return False
    return lower.startswith(("http://", "https://", "mailto:", "/", "#", "."))


def sanitize_editorial_article_html_with_warnings(html: str) -> SanitizeResult:
    """Sanitize article HTML and report what was removed."""
    if not html or not html.strip():
        return SanitizeResult(html="")
    cleaned = re.sub(r"<(script|style|iframe)[^>]*>.*?</\1>", "", html, flags=re.I | re.S)
    cleaned = re.sub(r"<(script|style|iframe)[^>]*/?>", "", cleaned, flags=re.I)
    parser = _SanitizingHTMLParser()
    try:
        # No unescape() here: escaped markup in the source is content, not tags.
        parser.feed(cleaned)
        parser.close()
    except Exception:
        return SanitizeResult(html=escape(html))
    return SanitizeResult(html=parser.get_html(), warnings=parser.get_warnings())


def sanitize_editorial_article_html(html: str) -> str:
    """Return HTML with only allowed editorial tags and safe link attributes."""
    return sanitize_editorial_article_html_with_warnings(html).html
