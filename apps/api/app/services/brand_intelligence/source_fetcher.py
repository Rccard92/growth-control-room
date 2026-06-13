"""Public URL fetch for Brand Intelligence external sources (v1 — lightweight)."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 10.0
MAX_TEXT_LENGTH = 8000
MAX_SUMMARY_LENGTH = 1200

USER_AGENT = (
    "Mozilla/5.0 (compatible; GrowthControlRoom/1.0; +https://growthcontrolroom.com/bot)"
)

SOCIAL_TYPES = frozenset(
    {"instagram", "facebook", "tiktok", "youtube", "linkedin"}
)
REVIEW_TYPES = frozenset({"trustpilot", "google_business"})

INACCESSIBLE_MESSAGE = (
    "Fonte non accessibile automaticamente. Puoi caricare screenshot/report o testo esportato."
)


class _MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self.meta_description: str | None = None
        self.og_title: str | None = None
        self.og_description: str | None = None
        self.headings: list[str] = []
        self._text_parts: list[str] = []
        self._in_title = False
        self._in_heading = False
        self._skip_tags = frozenset({"script", "style", "noscript"})

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {k: (v or "") for k, v in attrs}
        if tag == "title":
            self._in_title = True
        elif tag in ("h1", "h2", "h3"):
            self._in_heading = True
        elif tag == "meta":
            name = (attr_map.get("name") or attr_map.get("property") or "").lower()
            content = (attr_map.get("content") or "").strip()
            if not content:
                return
            if name in ("description", "og:description") and not self.meta_description:
                self.meta_description = content
            if name == "og:description":
                self.og_description = content
            if name in ("og:title", "twitter:title") and not self.og_title:
                self.og_title = content

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3"):
            self._in_heading = False

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_title and not self.title:
            self.title = text[:500]
        elif self._in_heading:
            self.headings.append(text[:300])
        else:
            self._text_parts.append(text)

    def body_text(self) -> str:
        return " ".join(self._text_parts)


def _truncate(text: str | None, limit: int) -> str | None:
    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _build_summary(
    title: str | None,
    meta: str | None,
    headings: list[str],
    body: str | None,
) -> str | None:
    parts: list[str] = []
    if title:
        parts.append(f"Title: {title}")
    if meta:
        parts.append(f"Description: {meta}")
    if headings:
        parts.append("Headings: " + "; ".join(headings[:5]))
    if body:
        parts.append(body[:600])
    if not parts:
        return None
    return _truncate(" | ".join(parts), MAX_SUMMARY_LENGTH)


def _parse_html_metadata(html: str) -> dict[str, Any]:
    parser = _MetadataParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return {"title": None, "meta_description": None, "headings": [], "text": None}

    meta = parser.og_description or parser.meta_description
    title = parser.og_title or parser.title
    body = _truncate(parser.body_text(), MAX_TEXT_LENGTH)
    return {
        "title": _truncate(title, 500),
        "meta_description": _truncate(meta, 1000),
        "headings": parser.headings[:10],
        "text": body,
    }


async def _http_get(url: str) -> tuple[int, str | None, str | None]:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    try:
        async with httpx.AsyncClient(
            timeout=FETCH_TIMEOUT,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=5),
        ) as client:
            response = await client.get(url, headers=headers)
            if response.status_code >= 400:
                return response.status_code, None, f"HTTP {response.status_code}"
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type.lower() and "text" not in content_type.lower():
                return response.status_code, None, "Contenuto non HTML/testo"
            return response.status_code, response.text, None
    except httpx.TimeoutException:
        return 0, None, "Timeout durante il recupero"
    except httpx.HTTPError as exc:
        return 0, None, str(exc)


async def _fetch_website(url: str) -> dict[str, Any]:
    status_code, html, error = await _http_get(url)
    if error or not html:
        return {
            "status": "failed",
            "fetch_error": error or INACCESSIBLE_MESSAGE,
            "fetched_title": None,
            "fetched_text": None,
            "fetched_summary": None,
        }
    parsed = _parse_html_metadata(html)
    summary = _build_summary(
        parsed.get("title"),
        parsed.get("meta_description"),
        parsed.get("headings") or [],
        parsed.get("text"),
    )
    if not summary and not parsed.get("text"):
        return {
            "status": "skipped",
            "fetch_error": INACCESSIBLE_MESSAGE,
            "fetched_title": parsed.get("title"),
            "fetched_text": None,
            "fetched_summary": None,
        }
    return {
        "status": "fetched",
        "fetch_error": None,
        "fetched_title": parsed.get("title"),
        "fetched_text": parsed.get("text"),
        "fetched_summary": summary,
    }


async def _fetch_social_metadata(url: str) -> dict[str, Any]:
    status_code, html, error = await _http_get(url)
    if error or not html:
        return {
            "status": "skipped",
            "fetch_error": error or INACCESSIBLE_MESSAGE,
            "fetched_title": None,
            "fetched_text": None,
            "fetched_summary": None,
        }
    parsed = _parse_html_metadata(html)
    title = parsed.get("title")
    meta = parsed.get("meta_description")
    if not title and not meta:
        return {
            "status": "skipped",
            "fetch_error": INACCESSIBLE_MESSAGE,
            "fetched_title": None,
            "fetched_text": None,
            "fetched_summary": None,
        }
    summary = _build_summary(title, meta, [], None)
    return {
        "status": "fetched",
        "fetch_error": None,
        "fetched_title": title,
        "fetched_text": _truncate(meta, 2000),
        "fetched_summary": summary,
    }


async def _fetch_review_platform(url: str) -> dict[str, Any]:
    status_code, html, error = await _http_get(url)
    if error or not html:
        return {
            "status": "failed",
            "fetch_error": error or INACCESSIBLE_MESSAGE,
            "fetched_title": None,
            "fetched_text": None,
            "fetched_summary": None,
        }
    parsed = _parse_html_metadata(html)
    text = parsed.get("text")
    if not text or len(text) < 80:
        return {
            "status": "skipped",
            "fetch_error": INACCESSIBLE_MESSAGE,
            "fetched_title": parsed.get("title"),
            "fetched_text": None,
            "fetched_summary": None,
        }
    summary = _build_summary(
        parsed.get("title"),
        parsed.get("meta_description"),
        parsed.get("headings") or [],
        text[:1500],
    )
    return {
        "status": "fetched",
        "fetch_error": None,
        "fetched_title": parsed.get("title"),
        "fetched_text": _truncate(text, MAX_TEXT_LENGTH),
        "fetched_summary": summary,
    }


async def fetch_url_content(source_type: str, url: str) -> dict[str, Any]:
    """Fetch public content for a single external source URL."""
    if source_type == "website":
        return await _fetch_website(url)
    if source_type in SOCIAL_TYPES:
        return await _fetch_social_metadata(url)
    if source_type in REVIEW_TYPES:
        return await _fetch_review_platform(url)
    return await _fetch_website(url)


def format_external_source_for_prompt(source: Any, *, excerpt_limit: int = 2000) -> str:
    """Format a BrandExternalSource row for AI prompts."""
    lines = [
        f"- id={source.id} type={source.source_type} url={source.url} status={source.status}",
    ]
    if source.fetched_summary:
        lines.append(f"  summary: {source.fetched_summary[:excerpt_limit]}")
    if source.fetched_text and source.status == "fetched":
        lines.append(f"  excerpt: {source.fetched_text[:excerpt_limit]}")
    if source.fetch_error and source.status in ("failed", "skipped"):
        lines.append(f"  note: {source.fetch_error}")
    return "\n".join(lines)
