"""Sitemap XML discovery for Growth Audit page inventory."""

from __future__ import annotations

import gzip
import logging
import re
from collections import deque
from typing import Any
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import httpx

from app.services.growth_audit.url_utils import (
    extract_domain,
    is_excluded_audit_url,
    normalize_root_url,
    normalize_url,
)

logger = logging.getLogger(__name__)

USER_AGENT = "GrowthControlRoomAuditBot/1.0"
MAX_SITEMAP_BYTES = 2 * 1024 * 1024
MAX_NESTED_SITEMAPS = 20
MAX_ROBOTS_SITEMAPS = 3
ROBOTS_SITEMAP_RE = re.compile(r"^Sitemap:\s*(\S+)", re.IGNORECASE | re.MULTILINE)


def _normalize_hostname(hostname: str) -> str:
    host = hostname.lower().strip().rstrip(".")
    if host.startswith("www."):
        return host[4:]
    return host


def _same_domain(url: str, root_domain: str) -> bool:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False
        return _normalize_hostname(hostname) == _normalize_hostname(root_domain)
    except Exception:
        return False


def _candidate_sitemap_urls(root_url: str) -> list[str]:
    normalized = normalize_root_url(root_url)
    base = normalized.rstrip("/")
    return [
        f"{base}/sitemap.xml",
        f"{base}/sitemap_index.xml",
        f"{base}/sitemap.xml.gz",
    ]


def _safe_limit_urls(urls: list[str], max_urls: int) -> list[str]:
    if max_urls <= 0:
        return []
    return urls[:max_urls]


def _find_elements_by_local_name(root: ElementTree.Element, local_name: str) -> list[ElementTree.Element]:
    return [element for element in root.iter() if element.tag.split("}")[-1] == local_name]


def _is_sitemap_index(root: ElementTree.Element) -> bool:
    return root.tag.split("}")[-1] == "sitemapindex" or bool(
        _find_elements_by_local_name(root, "sitemap")
    )


def _is_urlset(root: ElementTree.Element) -> bool:
    return root.tag.split("}")[-1] == "urlset" or bool(_find_elements_by_local_name(root, "url"))


def _parse_sitemap_xml(content: bytes) -> tuple[list[str], list[str]]:
    page_urls: list[str] = []
    nested_sitemaps: list[str] = []

    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError:
        return page_urls, nested_sitemaps

    if _is_sitemap_index(root):
        for sitemap_el in _find_elements_by_local_name(root, "sitemap"):
            for loc_el in _find_elements_by_local_name(sitemap_el, "loc"):
                if loc_el.text and loc_el.text.strip():
                    nested_sitemaps.append(loc_el.text.strip())
        return page_urls, nested_sitemaps

    if _is_urlset(root):
        for url_el in _find_elements_by_local_name(root, "url"):
            for loc_el in _find_elements_by_local_name(url_el, "loc"):
                if loc_el.text and loc_el.text.strip():
                    page_urls.append(loc_el.text.strip())
        return page_urls, nested_sitemaps

    for loc_el in _find_elements_by_local_name(root, "loc"):
        if loc_el.text and loc_el.text.strip():
            page_urls.append(loc_el.text.strip())

    return page_urls, nested_sitemaps


async def _fetch_text_url(
    client: httpx.AsyncClient,
    url: str,
) -> tuple[bytes | None, str | None]:
    try:
        response = await client.get(url)
        if response.status_code >= 400:
            return None, f"HTTP {response.status_code}"
        content = response.content
        if len(content) > MAX_SITEMAP_BYTES:
            return None, "Sitemap troppo grande"
        content_type = (response.headers.get("content-type") or "").lower()
        if url.endswith(".gz") or "gzip" in content_type:
            try:
                content = gzip.decompress(content)
            except OSError:
                return None, "Impossibile decomprimere sitemap gzip"
        if len(content) > MAX_SITEMAP_BYTES:
            return None, "Sitemap decompressa troppo grande"
        return content, None
    except httpx.TimeoutException:
        return None, "Timeout"
    except httpx.HTTPError as exc:
        return None, str(exc)


async def _discover_robots_sitemaps(
    client: httpx.AsyncClient,
    root_url: str,
) -> list[str]:
    normalized = normalize_root_url(root_url)
    robots_url = f"{normalized.rstrip('/')}/robots.txt"
    content, _error = await _fetch_text_url(client, robots_url)
    if not content:
        return []
    try:
        text = content.decode("utf-8", errors="replace")
    except Exception:
        return []
    matches = ROBOTS_SITEMAP_RE.findall(text)
    return matches[:MAX_ROBOTS_SITEMAPS]


def _append_unique_url(
    urls: list[str],
    seen: set[str],
    candidate: str,
    root_domain: str,
    max_urls: int,
) -> bool:
    if len(urls) >= max_urls:
        return False
    if not _same_domain(candidate, root_domain):
        return False
    if is_excluded_audit_url(candidate):
        return False
    try:
        normalized = normalize_url(candidate)
    except Exception:
        return False
    if normalized in seen:
        return False
    seen.add(normalized)
    urls.append(normalized)
    return True


async def discover_sitemap_urls(
    root_url: str,
    max_urls: int = 200,
    timeout_seconds: float = 12.0,
) -> tuple[list[str], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    discovered: list[str] = []
    seen: set[str] = set()

    try:
        normalized_root = normalize_root_url(root_url)
        root_domain = extract_domain(normalized_root)
    except Exception as exc:
        events.append(
            {
                "type": "sitemap_error",
                "message": f"URL root non valida per discovery sitemap: {exc}",
                "url": root_url,
                "count": 0,
            }
        )
        return [], events

    candidates = _candidate_sitemap_urls(normalized_root)
    queue: deque[str] = deque()
    visited_sitemaps: set[str] = set()

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=timeout_seconds,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        robots_sitemaps = await _discover_robots_sitemaps(client, normalized_root)
        for robots_sitemap in robots_sitemaps:
            if robots_sitemap not in candidates:
                candidates.append(robots_sitemap)

        for candidate in candidates:
            if candidate not in visited_sitemaps:
                queue.append(candidate)

        found_any_sitemap = False
        processed_sitemaps = 0

        while queue and processed_sitemaps < MAX_NESTED_SITEMAPS and len(discovered) < max_urls:
            sitemap_url = queue.popleft()
            if sitemap_url in visited_sitemaps:
                continue
            visited_sitemaps.add(sitemap_url)
            processed_sitemaps += 1

            content, error = await _fetch_text_url(client, sitemap_url)
            if content is None:
                if processed_sitemaps == 1 and not found_any_sitemap:
                    events.append(
                        {
                            "type": "sitemap_missing",
                            "message": f"Sitemap non disponibile: {error or 'non trovata'}",
                            "url": sitemap_url,
                            "count": 0,
                        }
                    )
                else:
                    events.append(
                        {
                            "type": "sitemap_error",
                            "message": f"Errore lettura sitemap: {error or 'sconosciuto'}",
                            "url": sitemap_url,
                            "count": 0,
                        }
                    )
                continue

            found_any_sitemap = True
            page_urls, nested_sitemaps = _parse_sitemap_xml(content)
            before_count = len(discovered)

            for page_url in page_urls:
                if len(discovered) >= max_urls:
                    break
                absolute_url = urljoin(normalized_root, page_url)
                _append_unique_url(discovered, seen, absolute_url, root_domain, max_urls)

            added = len(discovered) - before_count
            events.append(
                {
                    "type": "sitemap_found",
                    "message": f"Sitemap analizzata, {added} URL aggiunte.",
                    "url": sitemap_url,
                    "count": added,
                }
            )

            for nested in nested_sitemaps:
                if len(visited_sitemaps) + len(queue) >= MAX_NESTED_SITEMAPS:
                    break
                absolute_nested = urljoin(normalized_root, nested)
                if absolute_nested not in visited_sitemaps:
                    queue.append(absolute_nested)

    if not discovered and not any(event["type"] == "sitemap_found" for event in events):
        if not any(event["type"] == "sitemap_missing" for event in events):
            events.append(
                {
                    "type": "sitemap_missing",
                    "message": "Nessuna sitemap trovata per il dominio.",
                    "url": normalized_root,
                    "count": 0,
                }
            )

    if len(discovered) >= max_urls:
        events.append(
            {
                "type": "sitemap_limit_reached",
                "message": f"Raggiunto limite di {max_urls} URL da sitemap.",
                "url": normalized_root,
                "count": len(discovered),
            }
        )

    return _safe_limit_urls(discovered, max_urls), events
