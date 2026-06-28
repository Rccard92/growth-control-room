"""Whitelist HTML sanitizer for editorial article bodyHtml."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from html import escape, unescape

_ALLOWED_TAGS = frozenset(
    {"h2", "h3", "p", "ul", "ol", "li", "strong", "em", "a", "blockquote", "div"}
)
_ALLOWED_LINK_ATTRS = frozenset({"href", "title", "rel"})
_ALLOWED_DIV_CLASSES = frozenset(
    {
        "gcr-article-body",
        "gcr-article-note",
        "gcr-product-tip",
        "gcr-article-cta",
    }
)
_STRIP_TAGS = frozenset({"script", "style", "iframe", "object", "embed"})


class _SanitizingHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._tag_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in _STRIP_TAGS:
            return
        if tag_lower not in _ALLOWED_TAGS:
            return
        if tag_lower == "a":
            safe_attrs: list[tuple[str, str]] = []
            for name, value in attrs:
                if name.lower() not in _ALLOWED_LINK_ATTRS or value is None:
                    continue
                if name.lower() == "href" and not _is_safe_href(value):
                    continue
                safe_attrs.append((name.lower(), value))
            attr_str = "".join(f' {k}="{escape(v, quote=True)}"' for k, v in safe_attrs)
            self._parts.append(f"<{tag_lower}{attr_str}>")
        elif tag_lower == "div":
            class_value = _extract_div_class(attrs)
            if not class_value:
                return
            self._parts.append(f'<div class="{escape(class_value, quote=True)}">')
        else:
            self._parts.append(f"<{tag_lower}>")
        self._tag_stack.append(tag_lower)

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower not in _ALLOWED_TAGS:
            return
        while self._tag_stack:
            popped = self._tag_stack.pop()
            self._parts.append(f"</{popped}>")
            if popped == tag_lower:
                break

    def handle_data(self, data: str) -> None:
        if data:
            self._parts.append(escape(data))

    def handle_entityref(self, name: str) -> None:
        self._parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._parts.append(f"&#{name};")

    def get_html(self) -> str:
        while self._tag_stack:
            tag = self._tag_stack.pop()
            self._parts.append(f"</{tag}>")
        return "".join(self._parts)


def _extract_div_class(attrs: list[tuple[str, str | None]]) -> str | None:
    for name, value in attrs:
        if name.lower() != "class" or not value:
            continue
        for cls in value.split():
            normalized = cls.strip().lower()
            if normalized in _ALLOWED_DIV_CLASSES:
                return normalized
    return None


def _is_safe_href(href: str) -> bool:
    href = href.strip()
    if not href:
        return False
    lower = href.lower()
    if lower.startswith(("javascript:", "data:", "vbscript:")):
        return False
    return lower.startswith(("http://", "https://", "mailto:", "/", "#", "."))


def sanitize_editorial_article_html(html: str) -> str:
    """Return HTML with only allowed editorial tags and safe link attributes."""
    if not html or not html.strip():
        return ""
    cleaned = re.sub(r"<(script|style|iframe)[^>]*>.*?</\1>", "", html, flags=re.I | re.S)
    cleaned = re.sub(r"<(script|style|iframe)[^>]*/?>", "", cleaned, flags=re.I)
    parser = _SanitizingHTMLParser()
    try:
        parser.feed(unescape(cleaned))
        parser.close()
    except Exception:
        return escape(html)
    return parser.get_html()
