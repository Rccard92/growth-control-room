"""Tests for editorial article quality validation."""

from app.schemas.content_seo_editorial import EditorialArticlePayload, EditorialBriefPayload
from app.services.content.editorial_article_quality import validate_editorial_article_quality


def _sample_brief() -> EditorialBriefPayload:
    return EditorialBriefPayload(
        proposed_title="Test",
        max_h2=5,
        max_h3=3,
        structure_complexity="snella",
    )


def test_validate_warns_on_too_many_strong_tags() -> None:
    strongs = "".join(f"<p><strong>Concetto {i}</strong> test.</p>" for i in range(13))
    html = f'<div class="gcr-article-body"><h2>Sezione</h2>{strongs}<ul><li>Uno</li></ul></div>'
    payload = EditorialArticlePayload(
        title="Perché il miele cristallizza",
        body_html=html,
        cta="Scopri",
    )
    warnings, metrics, _ = validate_editorial_article_quality(
        payload.body_html,
        payload,
        _sample_brief(),
        "educational_article",
        has_verified_link_targets=True,
    )
    assert metrics.strong_count > 12
    assert any("6–9" in w or "Troppi" in w for w in warnings)


def test_validate_warns_on_few_strong_tags() -> None:
    payload = EditorialArticlePayload(
        title="Titolo naturale",
        body_html=(
            '<div class="gcr-article-body"><h2>Sezione</h2>'
            "<p>Testo senza grassetti.</p><ul><li>Uno</li></ul></div>"
        ),
        cta="Scopri",
    )
    warnings, metrics, _ = validate_editorial_article_quality(
        payload.body_html,
        payload,
        _sample_brief(),
        "educational_article",
    )
    assert metrics.strong_count < 6
    assert any("grassetti" in w.lower() for w in warnings)


def test_validate_warns_missing_body_wrapper() -> None:
    payload = EditorialArticlePayload(
        title="Titolo",
        body_html="<h2>Sezione</h2><p><strong>Uno</strong></p>",
        cta="Scopri",
    )
    warnings, _, _ = validate_editorial_article_quality(
        payload.body_html,
        payload,
        _sample_brief(),
        "educational_article",
    )
    assert any("gcr-article-body" in w for w in warnings)
