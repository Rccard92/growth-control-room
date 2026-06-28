"""Editorial publishing payload utils tests."""

import os
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.schemas.content_seo_editorial import EditorialArticlePayload, EditorialPublishingPayload
from app.services.content.editorial_publishing_utils import (
    DEFAULT_AUTHOR_FALLBACK,
    build_article_create_input,
    build_publishing_payload_from_article,
    format_shopify_publish_error,
    merge_article_into_publishing,
    normalize_publishing_payload,
    resolve_publishing_author,
    shopify_publish_http_status,
    validate_publishing_payload,
)


def _sample_article(*, author_name: str = "A cura di Davide") -> EditorialArticlePayload:
    return EditorialArticlePayload(
        title="Guida olio EVO",
        handle="guida-olio-evo",
        excerpt="Tutto sull'olio.",
        body_html="<h2>Intro</h2><p>Testo utile.</p>",
        seo_title="Olio EVO guida",
        meta_description="Meta desc",
        tags=["olio", "cucina"],
        author_name=author_name,
    )


def test_resolve_publishing_author_priority_chain() -> None:
    payload = EditorialPublishingPayload(author="Autore salvato")
    assert (
        resolve_publishing_author(
            payload,
            article_author_name="Articolo Author",
            shop_name="Shop Name",
            brand_name="Solmielato",
        )
        == "Articolo Author"
    )
    assert (
        resolve_publishing_author(
            payload,
            shop_name="Shop Name",
            brand_name="Solmielato",
        )
        == "Autore salvato"
    )
    assert (
        resolve_publishing_author(
            EditorialPublishingPayload(author=""),
            shop_name="Shop Name",
            brand_name="Solmielato",
        )
        == "Shop Name"
    )
    assert (
        resolve_publishing_author(
            EditorialPublishingPayload(author=""),
            brand_name="Solmielato",
        )
        == "Solmielato"
    )
    assert (
        resolve_publishing_author(EditorialPublishingPayload(author=""))
        == DEFAULT_AUTHOR_FALLBACK
    )


def test_build_publishing_payload_from_article_uses_default_author() -> None:
    payload = build_publishing_payload_from_article(
        _sample_article(author_name=""),
        brand_name="Solmielato",
    )
    assert payload.author == "Solmielato"


def test_validate_publishing_payload_requires_title_and_body() -> None:
    payload = EditorialPublishingPayload(title="", body_html="")
    errors = validate_publishing_payload(payload)
    assert "titolo" in errors[0].lower()
    assert any("html" in e.lower() for e in errors)


def test_validate_publishing_payload_for_publish_requires_blog_and_author() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    payload = payload.model_copy(update={"author": ""})
    errors = validate_publishing_payload(payload, for_publish=True)
    assert any("blog" in e.lower() for e in errors)
    assert any("autore" in e.lower() for e in errors)


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


def test_build_article_create_input_draft_requires_author() -> None:
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


def test_build_article_create_input_empty_author_raises() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    payload = payload.model_copy(update={"author": ""})
    with pytest.raises(ValueError, match="Autore obbligatorio"):
        build_article_create_input(payload, blog_gid="gid://shopify/Blog/99", mode="draft")


def test_build_article_create_input_omits_empty_optional_fields() -> None:
    payload = EditorialPublishingPayload(
        title="Titolo",
        body_html="<p>Ok</p>",
        author="Redazione Test",
        handle="",
        excerpt="",
        image_url=None,
        template_suffix=None,
        tags=[],
    )
    article_input = build_article_create_input(
        payload,
        blog_gid="gid://shopify/Blog/1",
        mode="draft",
    )
    assert "handle" not in article_input
    assert "summary" not in article_input
    assert "image" not in article_input
    assert "templateSuffix" not in article_input
    assert "tags" not in article_input


def test_format_shopify_publish_error_author_message() -> None:
    raw = (
        "Errore GraphQL Shopify: Variable $article of type ArticleCreateInput! "
        "was provided invalid value for author (Expected value to not be null)"
    )
    assert "author obbligatorio" in format_shopify_publish_error(raw).lower()


def test_shopify_publish_http_status_graphql_is_422() -> None:
    assert (
        shopify_publish_http_status("Errore GraphQL Shopify: invalid value for author")
        == 422
    )
    assert shopify_publish_http_status("Impossibile contattare Shopify.") == 502


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
