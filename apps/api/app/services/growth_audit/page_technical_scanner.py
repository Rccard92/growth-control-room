"""Lightweight deterministic technical page scanner for Growth Audit."""

from __future__ import annotations

import json
import logging
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx

from app.services.growth_audit.exceptions import GrowthAuditValidationError
from app.services.growth_audit.url_utils import normalize_url

logger = logging.getLogger(__name__)

USER_AGENT = "GrowthControlRoomAuditBot/1.0"
_SKIP_TAGS = frozenset({"script", "style", "noscript"})
_JSON_LD_SCRIPT_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def _normalize_hostname(hostname: str) -> str:
    host = hostname.lower().strip().rstrip(".")
    if host.startswith("www."):
        return host[4:]
    return host


def _same_domain(url: str, root_domain: str | None) -> bool:
    if not root_domain or not url:
        return False
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        return _normalize_hostname(hostname) == _normalize_hostname(root_domain)
    except Exception:
        return False


def _truncate_text(value: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(value) <= max_chars:
        return value
    return value[:max_chars]


def _is_html_content_type(content_type: str | None) -> bool:
    if not content_type:
        return True
    lowered = content_type.lower()
    return "html" in lowered or "xml" in lowered


class _TechnicalPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self.meta_description: str | None = None
        self.canonical: str | None = None
        self.h1s: list[str] = []
        self.robots_raw: str = ""
        self.robots_noindex = False
        self.robots_nofollow = False
        self.open_graph: dict[str, str] = {}
        self.images_total = 0
        self.images_missing_alt = 0
        self.links_internal = 0
        self.links_external = 0
        self._in_title = False
        self._in_h1 = False
        self._skip_depth = 0
        self._root_domain: str | None = None

    def set_root_domain(self, root_domain: str | None) -> None:
        self._root_domain = root_domain

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return

        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True
        elif tag == "meta":
            name = (attr_map.get("name") or "").lower()
            prop = (attr_map.get("property") or "").lower()
            content = (attr_map.get("content") or "").strip()
            if name == "description" and content and not self.meta_description:
                self.meta_description = content
            elif name == "robots" and content:
                self.robots_raw = content
                tokens = {token.strip().lower() for token in content.split(",")}
                self.robots_noindex = "noindex" in tokens
                self.robots_nofollow = "nofollow" in tokens
            elif prop.startswith("og:") and content:
                key = prop[3:]
                if key in ("title", "description", "image") and key not in self.open_graph:
                    self.open_graph[key] = content
        elif tag == "link":
            rel = (attr_map.get("rel") or "").lower()
            href = (attr_map.get("href") or "").strip()
            if rel == "canonical" and href and not self.canonical:
                self.canonical = href
        elif tag == "img":
            self.images_total += 1
            alt = (attr_map.get("alt") or "").strip()
            if not alt:
                self.images_missing_alt += 1
        elif tag == "a":
            href = (attr_map.get("href") or "").strip()
            if not href or href.startswith("#") or href.lower().startswith("javascript:"):
                return
            if href.startswith("/") or href.startswith("./") or href.startswith("../"):
                self.links_internal += 1
            elif _same_domain(href, self._root_domain):
                self.links_internal += 1
            elif href.startswith("http://") or href.startswith("https://"):
                self.links_external += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth > 0:
            return
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        text = data.strip()
        if not text:
            return
        if self._in_title and not self.title:
            self.title = text
        elif self._in_h1:
            self.h1s.append(text)


def _parse_html(html: str, *, root_domain: str | None) -> _TechnicalPageParser:
    parser = _TechnicalPageParser()
    parser.set_root_domain(root_domain)
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass
    return parser


def extract_title(html: str) -> str | None:
    return _parse_html(html, root_domain=None).title


def extract_meta_description(html: str) -> str | None:
    return _parse_html(html, root_domain=None).meta_description


def extract_canonical(html: str) -> str | None:
    return _parse_html(html, root_domain=None).canonical


def extract_h1s(html: str) -> list[str]:
    return _parse_html(html, root_domain=None).h1s


def extract_robots_meta(html: str) -> dict[str, Any]:
    parsed = _parse_html(html, root_domain=None)
    return {
        "noindex": parsed.robots_noindex,
        "nofollow": parsed.robots_nofollow,
        "raw": parsed.robots_raw,
    }


def _collect_json_ld_types(node: Any, types: list[str]) -> None:
    if isinstance(node, dict):
        node_type = node.get("@type")
        if isinstance(node_type, str):
            types.append(node_type)
        elif isinstance(node_type, list):
            types.extend(str(item) for item in node_type if item)
        graph = node.get("@graph")
        if graph is not None:
            _collect_json_ld_types(graph, types)
        for value in node.values():
            if isinstance(value, (dict, list)):
                _collect_json_ld_types(value, types)
    elif isinstance(node, list):
        for item in node:
            _collect_json_ld_types(item, types)


def extract_json_ld_types(html: str) -> dict[str, Any]:
    types: list[str] = []
    for match in _JSON_LD_SCRIPT_RE.finditer(html):
        raw_json = match.group(1).strip()
        if not raw_json:
            continue
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            continue
        _collect_json_ld_types(data, types)
    unique_types = list(dict.fromkeys(types))
    return {"jsonLdCount": len(unique_types), "types": unique_types}


def extract_open_graph(html: str) -> dict[str, str | None]:
    parsed = _parse_html(html, root_domain=None)
    return {
        "title": parsed.open_graph.get("title"),
        "description": parsed.open_graph.get("description"),
        "image": parsed.open_graph.get("image"),
    }


def count_images_alt(html: str) -> dict[str, int]:
    parsed = _parse_html(html, root_domain=None)
    return {"total": parsed.images_total, "missingAlt": parsed.images_missing_alt}


def count_links(html: str, root_domain: str | None) -> dict[str, int]:
    parsed = _parse_html(html, root_domain=root_domain)
    return {"internal": parsed.links_internal, "external": parsed.links_external}


def _build_checks(
    *,
    http_status: int | None,
    title: str | None,
    title_length: int,
    meta_description: str | None,
    meta_description_length: int,
    canonical_url: str | None,
    canonical_same_domain: bool,
    h1_count: int,
    robots: dict[str, Any],
    schema: dict[str, Any],
    open_graph: dict[str, str | None],
    images: dict[str, int],
) -> dict[str, bool]:
    return {
        "httpOk": http_status is not None and 200 <= http_status < 300,
        "hasTitle": bool(title),
        "titleLengthOk": 30 <= title_length <= 65 if title else False,
        "hasMetaDescription": bool(meta_description),
        "metaDescriptionLengthOk": 80 <= meta_description_length <= 165
        if meta_description
        else False,
        "hasCanonical": bool(canonical_url),
        "canonicalSameDomain": canonical_same_domain,
        "hasSingleH1": h1_count == 1,
        "hasNoindex": bool(robots.get("noindex")),
        "hasJsonLd": schema.get("jsonLdCount", 0) > 0,
        "hasOpenGraph": bool(
            open_graph.get("title") or open_graph.get("description") or open_graph.get("image")
        ),
        "imagesAltOk": images.get("missingAlt", 0) == 0,
    }


def _empty_scan(url: str, *, fetch_error: str | None = None, http_status: int | None = None) -> dict:
    return {
        "url": url,
        "finalUrl": url,
        "httpStatus": http_status,
        "fetchError": fetch_error,
        "title": None,
        "titleLength": 0,
        "metaDescription": None,
        "metaDescriptionLength": 0,
        "canonicalUrl": None,
        "h1": None,
        "h1Count": 0,
        "robots": {"noindex": False, "nofollow": False, "raw": ""},
        "schema": {"jsonLdCount": 0, "types": []},
        "openGraph": {"title": None, "description": None, "image": None},
        "images": {"total": 0, "missingAlt": 0},
        "links": {"internal": 0, "external": 0},
        "score": 0,
        "checks": _build_checks(
            http_status=http_status,
            title=None,
            title_length=0,
            meta_description=None,
            meta_description_length=0,
            canonical_url=None,
            canonical_same_domain=False,
            h1_count=0,
            robots={"noindex": False},
            schema={"jsonLdCount": 0},
            open_graph={},
            images={"missingAlt": 0},
        ),
        "findings": [],
        "tasks": [],
        "raw": {"contentType": None, "htmlChars": 0},
    }


async def scan_page_technical(
    url: str,
    *,
    page_type: str = "unknown",
    root_domain: str | None = None,
    timeout_seconds: float = 12.0,
    max_html_chars: int = 1_500_000,
) -> dict:
    try:
        normalized_url = normalize_url(url)
    except (GrowthAuditValidationError, Exception) as exc:
        result = _empty_scan(url, fetch_error=str(exc))
        result["score"] = 0
        return result

    fetch_error: str | None = None
    http_status: int | None = None
    final_url = normalized_url
    content_type: str | None = None
    html = ""

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout_seconds,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            response = await client.get(normalized_url)
            http_status = response.status_code
            final_url = str(response.url)
            content_type = response.headers.get("content-type")
            if _is_html_content_type(content_type):
                html = _truncate_text(response.text, max_html_chars)
            else:
                fetch_error = f"Non-HTML content type: {content_type or 'unknown'}"
    except httpx.TimeoutException:
        fetch_error = "Request timed out"
    except httpx.RequestError as exc:
        fetch_error = str(exc) or "Request failed"
    except Exception as exc:
        fetch_error = str(exc) or "Unexpected fetch error"
        logger.warning("Technical scan fetch failed for %s: %s", normalized_url, exc)

    if fetch_error and http_status is None:
        result = _empty_scan(normalized_url, fetch_error=fetch_error, http_status=http_status)
        result["finalUrl"] = final_url
        result["raw"] = {"contentType": content_type, "htmlChars": 0}
        return result

    if not html:
        result = _empty_scan(
            normalized_url,
            fetch_error=fetch_error or "Empty HTML response",
            http_status=http_status,
        )
        result["finalUrl"] = final_url
        result["raw"] = {"contentType": content_type, "htmlChars": 0}
        return result

    parsed = _parse_html(html, root_domain=root_domain)
    robots = {
        "noindex": parsed.robots_noindex,
        "nofollow": parsed.robots_nofollow,
        "raw": parsed.robots_raw,
    }
    schema = extract_json_ld_types(html)
    open_graph = {
        "title": parsed.open_graph.get("title"),
        "description": parsed.open_graph.get("description"),
        "image": parsed.open_graph.get("image"),
    }
    images = {"total": parsed.images_total, "missingAlt": parsed.images_missing_alt}
    links = {"internal": parsed.links_internal, "external": parsed.links_external}

    title = parsed.title
    title_length = len(title) if title else 0
    meta_description = parsed.meta_description
    meta_description_length = len(meta_description) if meta_description else 0
    canonical_url = parsed.canonical
    h1_count = len(parsed.h1s)
    h1 = parsed.h1s[0] if parsed.h1s else None
    canonical_same_domain = _same_domain(canonical_url or "", root_domain)

    checks = _build_checks(
        http_status=http_status,
        title=title,
        title_length=title_length,
        meta_description=meta_description,
        meta_description_length=meta_description_length,
        canonical_url=canonical_url,
        canonical_same_domain=canonical_same_domain,
        h1_count=h1_count,
        robots=robots,
        schema=schema,
        open_graph=open_graph,
        images=images,
    )

    return {
        "url": normalized_url,
        "finalUrl": final_url,
        "httpStatus": http_status,
        "fetchError": fetch_error,
        "title": title,
        "titleLength": title_length,
        "metaDescription": meta_description,
        "metaDescriptionLength": meta_description_length,
        "canonicalUrl": canonical_url,
        "h1": h1,
        "h1Count": h1_count,
        "robots": robots,
        "schema": schema,
        "openGraph": open_graph,
        "images": images,
        "links": links,
        "score": 0,
        "checks": checks,
        "findings": [],
        "tasks": [],
        "raw": {"contentType": content_type, "htmlChars": len(html)},
        "pageType": page_type,
    }
