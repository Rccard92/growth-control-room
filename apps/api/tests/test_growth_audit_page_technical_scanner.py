"""Tests for Growth Audit page technical scanner."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.growth_audit.page_technical_scanner import (
    count_images_alt,
    count_links,
    extract_canonical,
    extract_h1s,
    extract_json_ld_types,
    extract_meta_description,
    extract_open_graph,
    extract_robots_meta,
    extract_title,
    scan_page_technical,
)

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Test Page Title Here For SEO</title>
  <meta name="description" content="A meta description that is long enough to be useful for search engines and users clicking from results pages.">
  <meta name="robots" content="noindex, nofollow">
  <link rel="canonical" href="https://example.com/page">
  <meta property="og:title" content="OG Title">
  <meta property="og:description" content="OG Description">
  <meta property="og:image" content="https://example.com/image.jpg">
  <script type="application/ld+json">
  {"@context":"https://schema.org","@type":"Product","name":"Test"}
  </script>
  <script type="application/ld+json">
  {"@graph":[{"@type":"BreadcrumbList"},{"@type":"WebPage"}]}
  </script>
</head>
<body>
  <h1>Main Heading</h1>
  <h1>Second H1</h1>
  <img src="/a.jpg" alt="Good alt">
  <img src="/b.jpg">
  <img src="/c.jpg" alt="">
  <a href="/internal">Internal</a>
  <a href="https://example.com/other">Also internal</a>
  <a href="https://external.com/page">External</a>
  <a href="#anchor">Anchor</a>
</body>
</html>
"""


def test_extract_title() -> None:
    assert extract_title(SAMPLE_HTML) == "Test Page Title Here For SEO"


def test_extract_meta_description() -> None:
    desc = extract_meta_description(SAMPLE_HTML)
    assert desc is not None
    assert "meta description" in desc


def test_extract_canonical() -> None:
    assert extract_canonical(SAMPLE_HTML) == "https://example.com/page"


def test_extract_h1s() -> None:
    h1s = extract_h1s(SAMPLE_HTML)
    assert h1s == ["Main Heading", "Second H1"]


def test_extract_robots_meta() -> None:
    robots = extract_robots_meta(SAMPLE_HTML)
    assert robots["noindex"] is True
    assert robots["nofollow"] is True
    assert "noindex" in robots["raw"]


def test_extract_json_ld_types() -> None:
    schema = extract_json_ld_types(SAMPLE_HTML)
    assert schema["jsonLdCount"] >= 2
    assert "Product" in schema["types"]
    assert "BreadcrumbList" in schema["types"]


def test_extract_open_graph() -> None:
    og = extract_open_graph(SAMPLE_HTML)
    assert og["title"] == "OG Title"
    assert og["description"] == "OG Description"
    assert og["image"] == "https://example.com/image.jpg"


def test_count_images_alt() -> None:
    images = count_images_alt(SAMPLE_HTML)
    assert images["total"] == 3
    assert images["missingAlt"] == 2


def test_count_links() -> None:
    links = count_links(SAMPLE_HTML, "example.com")
    assert links["internal"] == 2
    assert links["external"] == 1


def test_handles_invalid_html() -> None:
    broken = "<html><title>Broken</title><h1>Unclosed"
    assert extract_title(broken) == "Broken"
    assert extract_h1s(broken) == ["Unclosed"]


def test_scan_page_technical_http_error() -> None:
    async def run() -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.url = "https://example.com/missing"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = "<html><title>Not Found</title></html>"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.services.growth_audit.page_technical_scanner.httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await scan_page_technical(
                "https://example.com/missing",
                root_domain="example.com",
            )

        assert result["httpStatus"] == 404
        assert result["title"] == "Not Found"
        assert result["checks"]["httpOk"] is False

    asyncio.run(run())


def test_scan_page_technical_fetch_timeout() -> None:
    async def run() -> None:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.services.growth_audit.page_technical_scanner.httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await scan_page_technical("https://example.com", root_domain="example.com")

        assert result["fetchError"] is not None
        assert result["httpStatus"] is None

    asyncio.run(run())


def test_scan_page_technical_success() -> None:
    async def run() -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://example.com/"
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.text = SAMPLE_HTML

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "app.services.growth_audit.page_technical_scanner.httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await scan_page_technical(
                "https://example.com/",
                page_type="product",
                root_domain="example.com",
            )

        assert result["httpStatus"] == 200
        assert result["title"] == "Test Page Title Here For SEO"
        assert result["h1Count"] == 2
        assert result["schema"]["types"]
        assert result["images"]["missingAlt"] == 2

    asyncio.run(run())
