"""Tests for Growth Audit sitemap discovery."""

from __future__ import annotations

import gzip
from unittest.mock import AsyncMock, patch

from app.services.growth_audit.sitemap_discovery import (
    _parse_sitemap_xml,
    discover_sitemap_urls,
)


URLSET_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/</loc></url>
  <url><loc>https://example.com/products/foo</loc></url>
  <url><loc>https://other.com/page</loc></url>
</urlset>
"""

INDEX_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-products.xml</loc></sitemap>
</sitemapindex>
"""


def test_parse_urlset_xml() -> None:
    urls, nested = _parse_sitemap_xml(URLSET_XML)
    assert len(urls) == 3
    assert nested == []


def test_parse_sitemapindex_xml() -> None:
    urls, nested = _parse_sitemap_xml(INDEX_XML)
    assert urls == []
    assert nested == ["https://example.com/sitemap-products.xml"]


def test_parse_invalid_xml_without_crash() -> None:
    urls, nested = _parse_sitemap_xml(b"not-xml")
    assert urls == []
    assert nested == []


def test_discover_sitemap_urls_respects_max_urls() -> None:
    async def run() -> None:
        async def fake_fetch(_client, url):
            if url.endswith("sitemap.xml"):
                many = "\n".join(
                    f"<url><loc>https://example.com/page-{index}</loc></url>"
                    for index in range(10)
                )
                content = f"""<?xml version="1.0"?><urlset>{many}</urlset>""".encode()
                return content, None
            return None, "missing"

        with patch(
            "app.services.growth_audit.sitemap_discovery._fetch_text_url",
            new=AsyncMock(side_effect=fake_fetch),
        ):
            urls, events = await discover_sitemap_urls("https://example.com", max_urls=3)

        assert len(urls) == 3
        assert any(event["type"] == "sitemap_limit_reached" for event in events)

    import asyncio

    asyncio.run(run())


def test_discover_sitemap_urls_ignores_external_domain() -> None:
    async def run() -> None:
        async def fake_fetch(_client, url):
            if url.endswith("sitemap.xml"):
                return URLSET_XML, None
            return None, "missing"

        with patch(
            "app.services.growth_audit.sitemap_discovery._fetch_text_url",
            new=AsyncMock(side_effect=fake_fetch),
        ):
            urls, _events = await discover_sitemap_urls("https://example.com", max_urls=10)

        assert "https://example.com/" in urls
        assert "https://example.com/products/foo" in urls
        assert all("other.com" not in url for url in urls)

    import asyncio

    asyncio.run(run())


def test_discover_sitemap_urls_handles_missing_sitemap() -> None:
    async def run() -> None:
        with patch(
            "app.services.growth_audit.sitemap_discovery._fetch_text_url",
            new=AsyncMock(return_value=(None, "HTTP 404")),
        ):
            urls, events = await discover_sitemap_urls("https://example.com", max_urls=10)

        assert urls == []
        assert any(event["type"] in {"sitemap_missing", "sitemap_error"} for event in events)

    import asyncio

    asyncio.run(run())


def test_fetch_text_url_decompresses_gzip_content() -> None:
    xml = b"<urlset><url><loc>https://example.com/</loc></url></urlset>"
    gz_content = gzip.compress(xml)

    async def run() -> None:
        from app.services.growth_audit.sitemap_discovery import _fetch_text_url

        class FakeResponse:
            status_code = 200
            content = gz_content
            headers = {"content-type": "application/gzip"}

        class FakeClient:
            async def get(self, _url):
                return FakeResponse()

        content, error = await _fetch_text_url(FakeClient(), "https://example.com/sitemap.xml.gz")
        assert error is None
        assert content == xml

    import asyncio

    asyncio.run(run())


def test_discover_sitemap_urls_parses_gzip_candidate() -> None:
    xml = b"<urlset><url><loc>https://example.com/pages/about</loc></url></urlset>"

    async def run() -> None:
        async def fake_fetch(_client, url):
            if url.endswith(".gz"):
                return xml, None
            return None, "missing"

        with patch(
            "app.services.growth_audit.sitemap_discovery._fetch_text_url",
            new=AsyncMock(side_effect=fake_fetch),
        ):
            urls, events = await discover_sitemap_urls("https://example.com", max_urls=10)

        assert "https://example.com/pages/about" in urls
        assert any(event["type"] == "sitemap_found" for event in events)

    import asyncio

    asyncio.run(run())
