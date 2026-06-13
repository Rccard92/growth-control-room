"""Source fetcher unit tests."""

from app.services.brand_intelligence.source_fetcher import (
    _build_summary,
    _parse_html_metadata,
    _truncate,
)


def test_parse_html_metadata_extracts_title_and_description() -> None:
    html = """
    <html><head>
    <title>Acme Brand</title>
    <meta name="description" content="We make great products." />
    </head><body><h1>Welcome</h1><p>Our story begins here.</p></body></html>
    """
    parsed = _parse_html_metadata(html)
    assert parsed["title"] == "Acme Brand"
    assert "great products" in (parsed["meta_description"] or "")
    assert parsed["text"]


def test_build_summary_combines_fields() -> None:
    summary = _build_summary("Title", "Meta desc", ["Heading"], "Body text here.")
    assert summary
    assert "Title" in summary


def test_truncate_limits_length() -> None:
    long = "a" * 100
    result = _truncate(long, 20)
    assert result is not None
    assert len(result) <= 20
