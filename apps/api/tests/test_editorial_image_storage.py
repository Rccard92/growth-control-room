"""Tests for editorial image storage."""

from uuid import uuid4

from app.services.content.editorial_image_storage import (
    delete_editorial_image,
    generate_access_token,
    is_shopify_image_publishable,
    read_editorial_image_bytes,
    resolve_preview_image_url,
    save_editorial_image,
)


def test_save_read_delete_editorial_image_local(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.content.editorial_image_storage.settings.editorial_images_dir",
        str(tmp_path),
    )
    monkeypatch.setattr(
        "app.services.content.editorial_image_storage.settings.editorial_image_storage_provider",
        "local",
    )
    project_id = uuid4()
    filename = "yogurt-con-frutta.jpg"
    data = b"fake-jpeg-bytes"
    storage_path, public_url, image_hash = save_editorial_image(project_id, filename, data)
    assert storage_path.endswith(filename)
    assert public_url is None
    assert image_hash
    assert read_editorial_image_bytes(storage_path) == data
    token = generate_access_token()
    url = resolve_preview_image_url(project_id, uuid4(), token)
    assert url is None
    monkeypatch.setattr(
        "app.services.content.editorial_image_storage.settings.public_api_base_url",
        "https://api.example.com",
    )
    url = resolve_preview_image_url(project_id, uuid4(), token)
    assert url is not None
    assert token in url
    delete_editorial_image(storage_path)
    try:
        read_editorial_image_bytes(storage_path)
        raised = False
    except FileNotFoundError:
        raised = True
    assert raised


def test_is_shopify_image_publishable_requires_cdn_url(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.content.editorial_image_storage.settings.editorial_image_public_base_url",
        "https://cdn.example.com/editorial",
    )
    assert is_shopify_image_publishable(
        "https://cdn.example.com/editorial/proj/editorial/test.jpg"
    )
    assert is_shopify_image_publishable(
        "https://cdn.shopify.com/s/files/1/123/files/hero.jpg"
    )
    assert is_shopify_image_publishable("https://cdn.shopifycdn.com/hero.jpg")
    assert not is_shopify_image_publishable(
        "https://api.example.com/projects/x/image-media?token=abc"
    )
    assert not is_shopify_image_publishable("http://localhost:8000/img.jpg")
    assert not is_shopify_image_publishable(None)
