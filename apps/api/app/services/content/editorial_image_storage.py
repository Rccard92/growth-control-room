"""Local and S3-compatible storage for editorial hero images."""

from __future__ import annotations

import hashlib
import secrets
from pathlib import Path
from uuid import UUID

from app.core.config import settings

PUBLIC_STORAGE_WARNING = (
    "Storage pubblico immagini non configurato: l'immagine non può essere inviata a Shopify."
)


def _images_root() -> Path:
    root = Path(settings.editorial_images_dir)
    if not root.is_absolute():
        api_root = Path(__file__).resolve().parents[3]
        root = api_root / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def _storage_provider() -> str:
    return (settings.editorial_image_storage_provider or "local").strip().lower()


def generate_access_token() -> str:
    return secrets.token_urlsafe(32)


def _build_storage_key(project_id: UUID, filename: str) -> str:
    safe_name = Path(filename).name
    return f"{project_id}/editorial/{safe_name}"


def _build_public_url(storage_key: str) -> str | None:
    base = (settings.editorial_image_public_base_url or "").strip().rstrip("/")
    if not base:
        return None
    return f"{base}/{storage_key}"


def _upload_to_s3(storage_key: str, image_bytes: bytes, content_type: str) -> None:
    import boto3
    from botocore.config import Config

    client_kwargs: dict = {
        "service_name": "s3",
        "aws_access_key_id": settings.editorial_image_s3_access_key,
        "aws_secret_access_key": settings.editorial_image_s3_secret_key,
        "region_name": settings.editorial_image_s3_region or "auto",
        "config": Config(signature_version="s3v4"),
    }
    endpoint = (settings.editorial_image_s3_endpoint_url or "").strip()
    if endpoint:
        client_kwargs["endpoint_url"] = endpoint

    client = boto3.client(**client_kwargs)
    client.put_object(
        Bucket=settings.editorial_image_s3_bucket,
        Key=storage_key,
        Body=image_bytes,
        ContentType=content_type,
        CacheControl="public, max-age=31536000, immutable",
    )


def save_editorial_image(
    project_id: UUID,
    filename: str,
    image_bytes: bytes,
    *,
    content_type: str = "image/jpeg",
) -> tuple[str, str | None, str]:
    """Save image bytes and return (storage_path, public_url, sha256 hash)."""
    storage_key = _build_storage_key(project_id, filename)
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    provider = _storage_provider()

    if provider == "s3":
        if not settings.editorial_image_s3_bucket:
            raise ValueError("EDITORIAL_IMAGE_S3_BUCKET non configurato.")
        _upload_to_s3(storage_key, image_bytes, content_type)
        public_url = _build_public_url(storage_key)
        return storage_key, public_url, image_hash

    target = _images_root() / storage_key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(image_bytes)
    return storage_key, None, image_hash


def delete_editorial_image(storage_path: str | None) -> None:
    if not storage_path:
        return
    provider = _storage_provider()
    if provider == "s3":
        if not settings.editorial_image_s3_bucket:
            return
        try:
            import boto3

            client_kwargs: dict = {
                "service_name": "s3",
                "aws_access_key_id": settings.editorial_image_s3_access_key,
                "aws_secret_access_key": settings.editorial_image_s3_secret_key,
                "region_name": settings.editorial_image_s3_region or "auto",
            }
            endpoint = (settings.editorial_image_s3_endpoint_url or "").strip()
            if endpoint:
                client_kwargs["endpoint_url"] = endpoint
            client = boto3.client(**client_kwargs)
            client.delete_object(Bucket=settings.editorial_image_s3_bucket, Key=storage_path)
        except Exception:
            return
        return

    path = _images_root() / storage_path
    if path.is_file():
        path.unlink(missing_ok=True)


def read_editorial_image_bytes(storage_path: str) -> bytes:
    provider = _storage_provider()
    if provider == "s3":
        if not settings.editorial_image_s3_bucket:
            raise FileNotFoundError(f"Bucket S3 non configurato: {storage_path}")
        import boto3

        client_kwargs: dict = {
            "service_name": "s3",
            "aws_access_key_id": settings.editorial_image_s3_access_key,
            "aws_secret_access_key": settings.editorial_image_s3_secret_key,
            "region_name": settings.editorial_image_s3_region or "auto",
        }
        endpoint = (settings.editorial_image_s3_endpoint_url or "").strip()
        if endpoint:
            client_kwargs["endpoint_url"] = endpoint
        client = boto3.client(**client_kwargs)
        response = client.get_object(Bucket=settings.editorial_image_s3_bucket, Key=storage_path)
        return response["Body"].read()

    path = _images_root() / storage_path
    if not path.is_file():
        raise FileNotFoundError(f"Immagine non trovata: {storage_path}")
    return path.read_bytes()


def resolve_preview_image_url(
    project_id: UUID,
    item_id: UUID,
    access_token: str,
) -> str | None:
    """Token-based preview URL for local storage (not valid for Shopify)."""
    base = (settings.public_api_base_url or "").strip().rstrip("/")
    if not base:
        return None
    if "localhost" in base or "127.0.0.1" in base:
        return None
    return (
        f"{base}/projects/{project_id}/content/seo/editorial-items/"
        f"{item_id}/image-media?token={access_token}"
    )


def resolve_authenticated_image_url(project_id: UUID, item_id: UUID) -> str:
    return (
        f"/projects/{project_id}/content/seo/editorial-items/"
        f"{item_id}/image-media"
    )


def is_public_storage_configured() -> bool:
    provider = _storage_provider()
    if provider != "s3":
        return False
    return bool(
        settings.editorial_image_s3_bucket
        and settings.editorial_image_public_base_url
        and settings.editorial_image_s3_access_key
        and settings.editorial_image_s3_secret_key
    )


def is_shopify_image_publishable(image_url: str | None) -> bool:
    if not image_url or not image_url.strip():
        return False
    url = image_url.strip().lower()
    if "localhost" in url or "127.0.0.1" in url:
        return False
    if "openai.com" in url or "oaidalle" in url:
        return False
    if "/image-media" in url or "token=" in url:
        return False
    public_base = (settings.editorial_image_public_base_url or "").strip().rstrip("/").lower()
    if not public_base:
        return False
    return url.startswith(public_base.lower() + "/") or url.startswith(public_base.lower())


def list_existing_filenames(project_id: UUID) -> set[str]:
    provider = _storage_provider()
    prefix = f"{project_id}/editorial/"
    names: set[str] = set()
    if provider == "s3":
        return names
    folder = _images_root() / prefix
    if not folder.is_dir():
        return names
    for path in folder.iterdir():
        if path.is_file():
            names.add(path.name)
    return names
