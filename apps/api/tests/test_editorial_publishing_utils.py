"""Editorial publishing payload utils tests."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.schemas.content_seo_editorial import EditorialArticlePayload, EditorialPublishingPayload
from app.services.content.editorial_publishing_utils import (
    build_article_create_input,
    build_publishing_payload_from_article,
    merge_article_into_publishing,
    normalize_publishing_payload,
    validate_publishing_payload,
)


def _sample_article() -> EditorialArticlePayload:
    return EditorialArticlePayload(
        title="Guida olio EVO",
        handle="guida-olio-evo",
        excerpt="Tutto sull'olio.",
        body_html="<h2>Intro</h2><p>Testo utile.</p>",
        seo_title="Olio EVO guida",
        meta_description="Meta desc",
        tags=["olio", "cucina"],
        author_name="A cura di Davide",
    )


def test_build_publishing_payload_from_article() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    assert payload.title == "Guida olio EVO"
    assert payload.body_html.startswith("<h2>")
    assert payload.author == "A cura di Davide"
    assert payload.mode == "draft"
    assert payload.is_published is False


def test_validate_publishing_payload_requires_title_and_body() -> None:
    payload = EditorialPublishingPayload(title="", body_html="")
    errors = validate_publishing_payload(payload)
    assert "titolo" in errors[0].lower()
    assert any("html" in e.lower() for e in errors)


def test_validate_publishing_payload_for_publish_requires_blog() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    errors = validate_publishing_payload(payload, for_publish=True)
    assert any("blog" in e.lower() for e in errors)


def test_merge_article_into_publishing_without_overwrite() -> None:
    existing = EditorialPublishingPayload(
        title="Titolo custom",
        body_html="<p>Custom</p>",
        blog_id="blog-uuid",
    )
    merged = merge_article_into_publishing(existing, _sample_article(), overwrite=False)
    assert merged.title == "Titolo custom"
    assert merged.body_html == "<p>Custom</p>"
    assert merged.blog_id == "blog-uuid"


def test_merge_article_into_publishing_with_overwrite() -> None:
    existing = EditorialPublishingPayload(
        title="Titolo custom",
        body_html="<p>Custom</p>",
        blog_id="blog-uuid",
        blog_gid="gid://shopify/Blog/1",
    )
    merged = merge_article_into_publishing(existing, _sample_article(), overwrite=True)
    assert merged.title == "Guida olio EVO"
    assert merged.blog_id == "blog-uuid"
    assert merged.blog_gid == "gid://shopify/Blog/1"


def test_build_article_create_input_draft() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    payload = payload.model_copy(update={"blog_gid": "gid://shopify/Blog/99"})
    article_input = build_article_create_input(
        payload,
        blog_gid="gid://shopify/Blog/99",
        mode="draft",
    )
    assert article_input["blogId"] == "gid://shopify/Blog/99"
    assert article_input["isPublished"] is False
    assert article_input["title"] == "Guida olio EVO"
    assert article_input["author"] == {"name": "A cura di Davide"}


def test_normalize_publishing_payload_camel_case() -> None:
    payload = normalize_publishing_payload(
        {
            "title": "Titolo",
            "bodyHtml": "<p>Ok</p>",
            "tags": "a, b",
            "mode": "publish_now",
        }
    )
    assert payload.body_html == "<p>Ok</p>"
    assert payload.tags == ["a", "b"]
    assert payload.mode == "publish_now"
