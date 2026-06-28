"""Tests for editorial article quality validation."""

from app.schemas.content_seo_editorial import EditorialArticlePayload, EditorialBriefPayload
from app.services.content.editorial_article_quality import (
    extract_html_blocks_used,
    validate_editorial_article_quality,
)


def _sample_brief() -> EditorialBriefPayload:
    return EditorialBriefPayload(
        proposed_title="Test",
        max_h2=5,
        max_h3=3,
        structure_complexity="snella",
    )


def test_extract_html_blocks_used() -> None:
    html = (
        '<div class="gcr-article-note"><strong>Da ricordare:</strong> test</div>'
        '<div class="gcr-product-tip"><strong>Consiglio:</strong> tip</div>'
    )
    blocks = extract_html_blocks_used(html)
    assert "gcr-article-note" in blocks
    assert "gcr-product-tip" in blocks


def test_validate_warns_on_few_strong_tags() -> None:
    payload = EditorialArticlePayload(
        title="T",
        body_html="<h2>Sezione</h2><p>Testo senza grassetti.</p><ul><li>Uno</li></ul>",
        cta="Scopri",
    )
    warnings, metrics = validate_editorial_article_quality(
        payload.body_html,
        payload,
        _sample_brief(),
        "educational_article",
    )
    assert metrics.strong_count < 4
    assert any("grassetti" in w.lower() for w in warnings)


def test_validate_warns_on_missing_list_for_educational() -> None:
    payload = EditorialArticlePayload(
        title="T",
        body_html=(
            "<h2>Sezione</h2>"
            "<p><strong>Uno</strong> <strong>Due</strong> "
            "<strong>Tre</strong> <strong>Quattro</strong>.</p>"
        ),
        cta="Scopri",
    )
    warnings, _ = validate_editorial_article_quality(
        payload.body_html,
        payload,
        _sample_brief(),
        "educational_article",
    )
    assert any("lista" in w.lower() for w in warnings)


def test_validate_warns_on_long_paragraphs() -> None:
    long_text = " ".join(["parola"] * 90)
    payload = EditorialArticlePayload(
        title="T",
        body_html=f"<p>{long_text}</p>",
        cta="Scopri",
    )
    warnings, metrics = validate_editorial_article_quality(
        payload.body_html,
        payload,
        _sample_brief(),
        "educational_article",
    )
    assert metrics.has_long_paragraphs is True
    assert any("paragrafi" in w.lower() for w in warnings)
