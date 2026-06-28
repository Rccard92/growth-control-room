"""Tests for editorial image utils."""

from app.schemas.content_seo_editorial import (
    EditorialApprovedImageBackup,
    EditorialArticlePayload,
    EditorialImagePayload,
    EditorialPublishingPayload,
)
from app.services.content.editorial_image_utils import (
    IMAGE_STALE_MESSAGE,
    compute_shopify_image_ready,
    is_image_filename_stale,
    is_image_publish_sync_stale,
    is_image_shopify_synced,
    is_image_stale,
    resolve_editorial_image_alt,
    sync_approved_image_to_publishing,
    sync_image_alt_from_article,
)


def test_is_image_stale_when_hashes_differ() -> None:
    assert is_image_stale(
        {"articleHash": "new-hash"},
        {"imageStatus": "generated", "sourceArticleHash": "old-hash"},
    )


def test_is_image_stale_false_when_not_generated() -> None:
    assert is_image_stale({"articleHash": "a"}, {"imageStatus": "not_generated"}) is False


def test_resolve_editorial_image_alt_priority() -> None:
    article = EditorialArticlePayload(title="Titolo articolo")
    assert (
        resolve_editorial_image_alt(article, {"proposedTitle": "Brief title"}, "Item title")
        == "Titolo articolo"
    )
    assert resolve_editorial_image_alt(None, {"proposedTitle": "Brief title"}, "Item title") == (
        "Brief title"
    )
    assert resolve_editorial_image_alt(None, None, "Item title") == "Item title"
    assert resolve_editorial_image_alt(None, None, None) == "Immagine articolo Solmielato"


def test_sync_image_alt_from_article() -> None:
    article = EditorialArticlePayload(title="Guida al miele")
    payload = EditorialImagePayload(image_status="generated")
    updated = sync_image_alt_from_article(payload, article)
    assert updated.image_alt == "Guida al miele"


def test_sync_approved_image_to_publishing_when_shopify_ready() -> None:
    publishing = EditorialPublishingPayload(title="Guida")
    image = EditorialImagePayload(
        image_status="approved",
        image_url="https://cdn.example.com/editorial/hero.jpg",
        image_alt="Guida al miele",
        shopify_image_ready=True,
    )
    updated = sync_approved_image_to_publishing(publishing, image)
    assert updated.image_url == "https://cdn.example.com/editorial/hero.jpg"
    assert updated.image_alt == "Guida al miele"


def test_sync_approved_image_skips_when_not_shopify_ready() -> None:
    publishing = EditorialPublishingPayload(title="Guida")
    image = EditorialImagePayload(
        image_status="approved",
        image_url=None,
        image_alt="Guida al miele",
        shopify_image_ready=False,
    )
    updated = sync_approved_image_to_publishing(publishing, image)
    assert updated.image_url is None


def test_sync_approved_image_uses_backup_when_regenerated() -> None:
    publishing = EditorialPublishingPayload(title="Guida")
    image = EditorialImagePayload(
        image_status="generated",
        image_url=None,
        shopify_image_ready=False,
        approved_image_backup=EditorialApprovedImageBackup(
            image_url="https://cdn.example.com/editorial/old.jpg",
            image_alt="Vecchio ALT",
            shopify_image_ready=True,
        ),
    )
    updated = sync_approved_image_to_publishing(publishing, image)
    assert updated.image_url == "https://cdn.example.com/editorial/old.jpg"
    assert updated.image_alt == "Vecchio ALT"


def test_is_image_filename_stale() -> None:
    image = EditorialImagePayload(
        image_filename="vecchio-titolo-articolo.jpg",
        image_status="approved",
    )
    assert is_image_filename_stale(image, "Nuovo titolo articolo completamente diverso")


def test_image_stale_message_constant() -> None:
    assert "non essere aggiornata" in IMAGE_STALE_MESSAGE


def test_compute_shopify_image_ready_delegates(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.content.editorial_image_utils.is_shopify_image_publishable",
        lambda url: url == "https://cdn.example.com/x.jpg",
    )
    assert compute_shopify_image_ready("https://cdn.example.com/x.jpg")
    assert not compute_shopify_image_ready("https://api.example.com/x")


def test_is_image_publish_sync_stale() -> None:
    image = EditorialImagePayload(
        image_status="approved",
        image_url="https://cdn.shopify.com/new.jpg",
        image_alt="Nuovo titolo",
    )
    publishing = EditorialPublishingPayload(
        title="Test",
        image_url="https://cdn.shopify.com/old.jpg",
        image_alt="Nuovo titolo",
    )
    assert is_image_publish_sync_stale(image, publishing)


def test_is_image_shopify_synced() -> None:
    synced = EditorialImagePayload(
        image_status="approved",
        image_approved_at="2026-06-01T10:00:00+00:00",
        shopify_image_synced_at="2026-06-01T11:00:00+00:00",
        shopify_image_ready=True,
    )
    assert is_image_shopify_synced(synced)
