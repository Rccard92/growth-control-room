"""Editorial publishing payload utils tests."""

import os
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

from app.schemas.content_seo_editorial import EditorialArticlePayload, EditorialPublishingPayload
from app.services.content.editorial_publishing_utils import (
    DEFAULT_AUTHOR_FALLBACK,
    HANDLE_CONFLICT_MESSAGE,
    PUBLISHING_STALE_MESSAGE,
    SEO_REQUIRED_MESSAGE,
    attach_publishing_sync_metadata,
    build_article_create_input,
    build_article_seo_metafields,
    build_article_update_input,
    classify_shopify_publish_error_code,
    build_publishing_payload_from_article,
    compute_editorial_article_hash,
    enrich_article_with_hash,
    format_handle_conflict_error,
    format_shopify_publish_error,
    is_publishing_stale,
    merge_article_into_publishing,
    normalize_publishing_payload,
    resolve_publishing_author,
    shopify_publish_http_status,
    validate_publishing_payload,
    validate_publishing_seo,
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


def test_compute_editorial_article_hash_stable() -> None:
    article = _sample_article()
    assert compute_editorial_article_hash(article) == compute_editorial_article_hash(article)


def test_enrich_article_with_hash() -> None:
    enriched = enrich_article_with_hash(_sample_article(), is_new_generation=True)
    assert enriched.article_hash
    assert enriched.generated_at
    assert enriched.updated_at


def test_build_article_update_input_publish_now() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    update_input = build_article_update_input(payload, mode="publish_now")
    assert "blogId" not in update_input
    assert update_input["isPublished"] is True
    assert "publishDate" not in update_input


def test_build_article_create_input_publish_now() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    article_input = build_article_create_input(
        payload,
        blog_gid="gid://shopify/Blog/99",
        mode="publish_now",
    )
    assert article_input["isPublished"] is True
    assert "publishDate" not in article_input


def test_build_article_create_input_draft() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    payload = payload.model_copy(update={"publish_date": "2026-07-05T09:00:00+02:00"})
    article_input = build_article_create_input(
        payload,
        blog_gid="gid://shopify/Blog/99",
        mode="draft",
    )
    assert article_input["isPublished"] is False
    assert "publishDate" not in article_input


def test_format_shopify_publish_error_schedule_is_published_conflict() -> None:
    raw = "Can't set isPublished to true and also set a future publish date."
    formatted = format_shopify_publish_error(raw)
    assert "modalità Programmato" in formatted
    assert (
        classify_shopify_publish_error_code(raw) == "shopify_schedule_is_published_conflict"
    )


def test_format_handle_conflict_error() -> None:
    assert format_handle_conflict_error("Handle already taken") == HANDLE_CONFLICT_MESSAGE


def test_is_publishing_stale_when_hashes_differ() -> None:
    article = enrich_article_with_hash(_sample_article(), is_new_generation=True)
    publishing = build_publishing_payload_from_article(article)
    publishing = attach_publishing_sync_metadata(publishing, article)
    stale_article = article.model_copy(update={"title": "Titolo aggiornato"})
    stale_article = enrich_article_with_hash(stale_article, is_new_generation=False)
    assert is_publishing_stale(stale_article, publishing) is True


def test_is_publishing_stale_when_source_hash_missing() -> None:
    article = enrich_article_with_hash(_sample_article(), is_new_generation=True)
    publishing = build_publishing_payload_from_article(article)
    assert is_publishing_stale(article, publishing) is True


def test_is_publishing_stale_false_when_synced() -> None:
    article = enrich_article_with_hash(_sample_article(), is_new_generation=True)
    publishing = build_publishing_payload_from_article(article)
    publishing = attach_publishing_sync_metadata(publishing, article)
    assert is_publishing_stale(article, publishing) is False


def test_is_publishing_stale_false_without_payloads() -> None:
    assert is_publishing_stale(None, None) is False
    assert is_publishing_stale(_sample_article(), None) is False


def test_publishing_stale_message_constant() -> None:
    assert "pubblicazione" in PUBLISHING_STALE_MESSAGE.lower()


def test_build_article_seo_metafields_global_keys() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    metafields = build_article_seo_metafields(payload)
    assert len(metafields) == 2
    keys = {entry["key"] for entry in metafields}
    assert keys == {"title_tag", "description_tag"}
    assert all(entry["namespace"] == "global" for entry in metafields)


def test_build_article_create_input_has_metafields_not_seo() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    article_input = build_article_create_input(
        payload,
        blog_gid="gid://shopify/Blog/99",
        mode="draft",
    )
    assert "seo" not in article_input
    assert "metafields" in article_input
    assert len(article_input["metafields"]) == 2


def test_build_article_update_input_has_metafields_not_seo() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    update_input = build_article_update_input(payload, mode="draft")
    assert "seo" not in update_input
    assert "metafields" in update_input


def test_build_article_create_input_includes_image_when_url_present() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    payload = payload.model_copy(
        update={
            "image_url": "https://cdn.example.com/editorial/hero.jpg",
            "image_alt": "Guida olio EVO",
        }
    )
    article_input = build_article_create_input(
        payload,
        blog_gid="gid://shopify/Blog/99",
        mode="draft",
    )
    assert article_input["image"] == {
        "url": "https://cdn.example.com/editorial/hero.jpg",
        "altText": "Guida olio EVO",
    }


def test_build_article_create_input_omits_image_without_url() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    article_input = build_article_create_input(
        payload,
        blog_gid="gid://shopify/Blog/99",
        mode="draft",
    )
    assert "image" not in article_input


def test_validate_publishing_seo_requires_fields_for_publish() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    payload = payload.model_copy(update={"seo_title": "", "meta_description": ""})
    errors, warnings = validate_publishing_seo(payload, for_publish=True)
    assert SEO_REQUIRED_MESSAGE in errors
    assert warnings == []


def test_validate_publishing_seo_length_warnings_only() -> None:
    payload = build_publishing_payload_from_article(_sample_article())
    payload = payload.model_copy(
        update={
            "seo_title": "x" * 61,
            "meta_description": "y" * 161,
        }
    )
    errors, warnings = validate_publishing_seo(payload, for_publish=True)
    assert errors == []
    assert len(warnings) == 2
