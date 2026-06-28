"""Build and validate editorial publishing payloads for Shopify."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

from app.schemas.content_seo_editorial import (
    EditorialArticlePayload,
    EditorialPublishingPayload,
    EditorialPublishMode,
)

_GID_NUMERIC_RE = re.compile(r"/(\d+)$")
DEFAULT_AUTHOR_FALLBACK = "Redazione Solmielato"
HANDLE_CONFLICT_MESSAGE = (
    "Esiste già un articolo Shopify con questo handle. "
    "Cambia handle o collega l'articolo esistente."
)
PUBLISHING_STALE_MESSAGE = (
    "I dati di pubblicazione non sono aggiornati rispetto all'articolo. "
    "Aggiorna i dati di pubblicazione prima di inviare a Shopify."
)
SEO_TITLE_RECOMMENDED_MAX = 60
META_DESCRIPTION_RECOMMENDED_MAX = 160
SEO_REQUIRED_MESSAGE = (
    "SEO title e meta description sono obbligatori per pubblicare un articolo completo."
)
ARTICLE_SEO_METAFIELD_NAMESPACE = "global"
ARTICLE_SEO_TITLE_KEY = "title_tag"
ARTICLE_SEO_DESCRIPTION_KEY = "description_tag"
ARTICLE_SEO_TITLE_TYPE = "single_line_text_field"
ARTICLE_SEO_DESCRIPTION_TYPE = "multi_line_text_field"


def _payload_is_present(payload: dict | EditorialArticlePayload | EditorialPublishingPayload | None) -> bool:
    if payload is None:
        return False
    if isinstance(payload, (EditorialArticlePayload, EditorialPublishingPayload)):
        return True
    return isinstance(payload, dict) and len(payload) > 0


def _read_str_field(
    payload: dict | EditorialArticlePayload | EditorialPublishingPayload,
    *keys: str,
) -> str:
    if isinstance(payload, EditorialArticlePayload):
        mapping = {
            "articleHash": payload.article_hash,
            "article_hash": payload.article_hash,
        }
        for key in keys:
            if key in mapping:
                return str(mapping[key] or "").strip()
        return ""
    if isinstance(payload, EditorialPublishingPayload):
        mapping = {
            "sourceArticleHash": payload.source_article_hash or "",
            "source_article_hash": payload.source_article_hash or "",
        }
        for key in keys:
            if key in mapping:
                return str(mapping[key] or "").strip()
        return ""
    for key in keys:
        raw = payload.get(key)
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    return ""


def is_publishing_stale(
    article_payload: dict | EditorialArticlePayload | None,
    publishing_payload: dict | EditorialPublishingPayload | None,
) -> bool:
    """True when article and publishing exist but sync metadata/hash are missing or divergent."""
    if not _payload_is_present(article_payload) or not _payload_is_present(publishing_payload):
        return False
    source_hash = _read_str_field(
        publishing_payload,  # type: ignore[arg-type]
        "sourceArticleHash",
        "source_article_hash",
    )
    article_hash = _read_str_field(
        article_payload,  # type: ignore[arg-type]
        "articleHash",
        "article_hash",
    )
    if not source_hash or not article_hash:
        return True
    return article_hash != source_hash


def _article_hash_fields(article: EditorialArticlePayload | dict[str, Any]) -> dict[str, str]:
    if isinstance(article, EditorialArticlePayload):
        tags = sorted(str(t).strip() for t in (article.tags or []) if str(t).strip())
        return {
            "title": article.title.strip(),
            "handle": article.handle.strip(),
            "bodyHtml": article.body_html.strip(),
            "excerpt": article.excerpt.strip(),
            "seoTitle": article.seo_title.strip(),
            "metaDescription": article.meta_description.strip(),
            "tags": ",".join(tags),
            "authorName": (article.author_name or "").strip(),
        }
    tags = sorted(str(t).strip() for t in (article.get("tags") or []) if str(t).strip())
    return {
        "title": str(article.get("title") or "").strip(),
        "handle": str(article.get("handle") or "").strip(),
        "bodyHtml": str(article.get("bodyHtml") or article.get("body_html") or "").strip(),
        "excerpt": str(article.get("excerpt") or "").strip(),
        "seoTitle": str(article.get("seoTitle") or article.get("seo_title") or "").strip(),
        "metaDescription": str(
            article.get("metaDescription") or article.get("meta_description") or ""
        ).strip(),
        "tags": ",".join(tags),
        "authorName": str(article.get("authorName") or article.get("author_name") or "").strip(),
    }


def compute_editorial_article_hash(article: EditorialArticlePayload | dict[str, Any]) -> str:
    """SHA-256 hex of canonical article content fields."""
    canonical = json.dumps(_article_hash_fields(article), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def enrich_article_with_hash(
    payload: EditorialArticlePayload,
    *,
    now: datetime | None = None,
    is_new_generation: bool = False,
) -> EditorialArticlePayload:
    """Attach articleHash and updatedAt; set generatedAt on first generation."""
    ts = (now or datetime.now(UTC)).isoformat()
    article_hash = compute_editorial_article_hash(payload)
    updates: dict[str, Any] = {
        "article_hash": article_hash,
        "updated_at": ts,
    }
    if is_new_generation or not (payload.generated_at or "").strip():
        updates["generated_at"] = ts
    return payload.model_copy(update=updates)


def attach_publishing_sync_metadata(
    publishing: EditorialPublishingPayload,
    article: EditorialArticlePayload,
    *,
    synced_at: datetime | None = None,
) -> EditorialPublishingPayload:
    ts = (synced_at or datetime.now(UTC)).isoformat()
    return publishing.model_copy(
        update={
            "source_article_hash": article.article_hash or compute_editorial_article_hash(article),
            "source_article_updated_at": article.updated_at or article.generated_at or ts,
            "synced_from_article_at": ts,
        }
    )


def shopify_gid_numeric_id(gid: str | None) -> str | None:
    if not gid:
        return None
    match = _GID_NUMERIC_RE.search(gid.strip())
    return match.group(1) if match else None


def _coerce_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def resolve_publishing_author(
    payload: EditorialPublishingPayload,
    *,
    article_author_name: str | None = None,
    shop_name: str | None = None,
    brand_name: str | None = None,
) -> str:
    for candidate in (
        article_author_name,
        payload.author,
        shop_name,
        brand_name,
        f"Redazione {brand_name}" if brand_name else None,
        DEFAULT_AUTHOR_FALLBACK,
    ):
        if candidate and str(candidate).strip():
            return str(candidate).strip()
    return DEFAULT_AUTHOR_FALLBACK


def normalize_publishing_payload(raw: dict[str, Any]) -> EditorialPublishingPayload:
    data = dict(raw)
    alias_map = {
        "bodyHtml": "body_html",
        "seoTitle": "seo_title",
        "metaDescription": "meta_description",
        "blogId": "blog_id",
        "blogGid": "blog_gid",
        "imageUrl": "image_url",
        "imageAlt": "image_alt",
        "isPublished": "is_published",
        "publishDate": "publish_date",
        "templateSuffix": "template_suffix",
    }
    for alias, field in alias_map.items():
        if alias in data and field not in data:
            data[field] = data.pop(alias)
    if "tags" in data:
        data["tags"] = _coerce_tags(data["tags"])
    else:
        data.setdefault("tags", [])
    for field in (
        "title",
        "handle",
        "body_html",
        "excerpt",
        "seo_title",
        "meta_description",
        "author",
    ):
        if field in data and data[field] is not None:
            data[field] = str(data[field])
        else:
            data.setdefault(field, "")
    for alias, field in (
        ("sourceArticleHash", "source_article_hash"),
        ("sourceArticleUpdatedAt", "source_article_updated_at"),
        ("syncedFromArticleAt", "synced_from_article_at"),
        ("shopifySeoSyncedAt", "shopify_seo_synced_at"),
        ("shopifySeoError", "shopify_seo_error"),
    ):
        if alias in data and field not in data:
            data[field] = data.pop(alias)
        elif field in data and data[field] is not None:
            data[field] = str(data[field])
    if "shopifySeoSynced" in data and "shopify_seo_synced" not in data:
        data["shopify_seo_synced"] = data.pop("shopifySeoSynced")
    elif "shopify_seo_synced" in data and data["shopify_seo_synced"] is not None:
        data["shopify_seo_synced"] = bool(data["shopify_seo_synced"])
    mode = data.get("mode", "draft")
    if mode not in ("draft", "publish_now", "schedule"):
        data["mode"] = "draft"
    data.setdefault("is_published", False)
    return EditorialPublishingPayload.model_validate(data)


def build_publishing_payload_from_article(
    article: EditorialArticlePayload | dict[str, Any],
    *,
    default_blog_id: str | None = None,
    default_blog_gid: str | None = None,
    shop_name: str | None = None,
    brand_name: str | None = None,
) -> EditorialPublishingPayload:
    if isinstance(article, dict):
        article = EditorialArticlePayload.model_validate(
            {
                "title": article.get("title", ""),
                "handle": article.get("handle", ""),
                "excerpt": article.get("excerpt", ""),
                "body_html": article.get("bodyHtml") or article.get("body_html", ""),
                "body_markdown": article.get("bodyMarkdown") or article.get("body_markdown", ""),
                "seo_title": article.get("seoTitle") or article.get("seo_title", ""),
                "meta_description": article.get("metaDescription")
                or article.get("meta_description", ""),
                "tags": article.get("tags") or [],
                "author_name": article.get("authorName") or article.get("author_name", ""),
            }
        )
    draft = EditorialPublishingPayload(
        title=article.title.strip(),
        handle=article.handle.strip(),
        body_html=article.body_html.strip(),
        excerpt=article.excerpt.strip(),
        seo_title=article.seo_title.strip() or article.title.strip(),
        meta_description=article.meta_description.strip(),
        author=(article.author_name or "").strip(),
        blog_id=default_blog_id,
        blog_gid=default_blog_gid,
        tags=list(article.tags or []),
        mode="draft",
        is_published=False,
        publish_date=None,
    )
    author = resolve_publishing_author(
        draft,
        article_author_name=article.author_name,
        shop_name=shop_name,
        brand_name=brand_name,
    )
    return draft.model_copy(update={"author": author})


def merge_article_into_publishing(
    existing: EditorialPublishingPayload | dict[str, Any],
    article: EditorialArticlePayload | dict[str, Any],
    *,
    overwrite: bool = False,
    shop_name: str | None = None,
    brand_name: str | None = None,
) -> EditorialPublishingPayload:
    base = (
        normalize_publishing_payload(existing)
        if isinstance(existing, dict)
        else existing
    )
    built = build_publishing_payload_from_article(
        article,
        shop_name=shop_name,
        brand_name=brand_name,
    )
    if overwrite:
        return built.model_copy(
            update={
                "blog_id": base.blog_id,
                "blog_gid": base.blog_gid,
                "mode": base.mode,
                "is_published": base.is_published,
                "publish_date": base.publish_date,
                "image_url": base.image_url,
                "image_alt": base.image_alt,
                "template_suffix": base.template_suffix,
            }
        )
    updates: dict[str, Any] = {}
    for field in (
        "title",
        "handle",
        "body_html",
        "excerpt",
        "seo_title",
        "meta_description",
        "author",
        "tags",
    ):
        current = getattr(base, field)
        incoming = getattr(built, field)
        if not current and incoming:
            updates[field] = incoming
    if not base.author and built.author:
        updates["author"] = built.author
    return base.model_copy(update=updates)


def build_article_seo_metafields(payload: EditorialPublishingPayload) -> list[dict[str, str]]:
    """Build Shopify Article metafields for SEO title and meta description."""
    metafields: list[dict[str, str]] = []
    seo_title = payload.seo_title.strip()
    meta_description = payload.meta_description.strip()
    if seo_title:
        metafields.append(
            {
                "namespace": ARTICLE_SEO_METAFIELD_NAMESPACE,
                "key": ARTICLE_SEO_TITLE_KEY,
                "type": ARTICLE_SEO_TITLE_TYPE,
                "value": seo_title,
            }
        )
    if meta_description:
        metafields.append(
            {
                "namespace": ARTICLE_SEO_METAFIELD_NAMESPACE,
                "key": ARTICLE_SEO_DESCRIPTION_KEY,
                "type": ARTICLE_SEO_DESCRIPTION_TYPE,
                "value": meta_description,
            }
        )
    return metafields


def validate_publishing_seo(
    payload: EditorialPublishingPayload | dict[str, Any],
    *,
    for_publish: bool = False,
) -> tuple[list[str], list[str]]:
    normalized = (
        normalize_publishing_payload(payload)
        if isinstance(payload, dict)
        else payload
    )
    errors: list[str] = []
    warnings: list[str] = []
    seo_title = normalized.seo_title.strip()
    meta_description = normalized.meta_description.strip()

    if for_publish:
        if not seo_title or not meta_description:
            errors.append(SEO_REQUIRED_MESSAGE)
        if not normalized.handle.strip():
            errors.append("Handle obbligatorio per pubblicare su Shopify.")

    if seo_title and len(seo_title) > SEO_TITLE_RECOMMENDED_MAX:
        warnings.append(
            f"SEO title lungo ({len(seo_title)} caratteri; consigliati max {SEO_TITLE_RECOMMENDED_MAX})."
        )
    if meta_description and len(meta_description) > META_DESCRIPTION_RECOMMENDED_MAX:
        warnings.append(
            "Meta description lunga "
            f"({len(meta_description)} caratteri; consigliati max {META_DESCRIPTION_RECOMMENDED_MAX})."
        )
    return errors, warnings


def validate_publishing_payload(
    payload: EditorialPublishingPayload | dict[str, Any],
    *,
    for_publish: bool = False,
    scheduled_publish_at: datetime | None = None,
) -> list[str]:
    normalized = (
        normalize_publishing_payload(payload)
        if isinstance(payload, dict)
        else payload
    )
    errors: list[str] = []
    if not normalized.title.strip():
        errors.append("Il titolo è obbligatorio.")
    if not normalized.body_html.strip():
        errors.append("Il contenuto HTML è obbligatorio.")
    if for_publish and not normalized.blog_id and not normalized.blog_gid:
        errors.append("Seleziona un blog Shopify prima di pubblicare.")
    if for_publish and not normalized.author.strip():
        errors.append("Autore obbligatorio per creare l'articolo su Shopify.")
    if for_publish and normalized.mode == "schedule":
        errors.append("La pubblicazione programmata non è ancora disponibile.")
        if scheduled_publish_at is None:
            errors.append("Data di pubblicazione programmata obbligatoria.")
        else:
            checked = scheduled_publish_at
            if checked.tzinfo is None:
                checked = checked.replace(tzinfo=UTC)
            if checked <= datetime.now(UTC):
                errors.append("La data di pubblicazione programmata deve essere futura.")
    seo_errors, _seo_warnings = validate_publishing_seo(normalized, for_publish=for_publish)
    errors.extend(seo_errors)
    return errors


def get_publishing_seo_warnings(
    payload: EditorialPublishingPayload | dict[str, Any],
) -> list[str]:
    _, warnings = validate_publishing_seo(payload, for_publish=False)
    return warnings


def validate_publishing_payload_with_warnings(
    payload: EditorialPublishingPayload | dict[str, Any],
    *,
    for_publish: bool = False,
    scheduled_publish_at: datetime | None = None,
) -> tuple[list[str], list[str]]:
    errors = validate_publishing_payload(
        payload,
        for_publish=for_publish,
        scheduled_publish_at=scheduled_publish_at,
    )
    _, seo_warnings = validate_publishing_seo(
        normalize_publishing_payload(payload) if isinstance(payload, dict) else payload,
        for_publish=for_publish,
    )
    return errors, seo_warnings


def _attach_seo_metafields_to_input(
    article_input: dict[str, Any],
    payload: EditorialPublishingPayload,
) -> None:
    metafields = build_article_seo_metafields(payload)
    if metafields:
        article_input["metafields"] = metafields


def build_article_create_input(
    payload: EditorialPublishingPayload,
    *,
    blog_gid: str,
    mode: EditorialPublishMode,
) -> dict[str, Any]:
    from datetime import datetime, timezone

    author = payload.author.strip()
    if not author:
        raise ValueError("Autore obbligatorio per Shopify articleCreate.")

    article_input: dict[str, Any] = {
        "blogId": blog_gid,
        "title": payload.title.strip(),
        "body": payload.body_html.strip(),
        "author": {"name": author},
    }
    if payload.handle.strip():
        article_input["handle"] = payload.handle.strip()
    if payload.excerpt.strip():
        article_input["summary"] = payload.excerpt.strip()
    if payload.tags:
        article_input["tags"] = payload.tags
    if payload.template_suffix and payload.template_suffix.strip():
        article_input["templateSuffix"] = payload.template_suffix.strip()
    if payload.image_url and payload.image_url.strip():
        image: dict[str, str] = {"url": payload.image_url.strip()}
        if payload.image_alt and payload.image_alt.strip():
            image["altText"] = payload.image_alt.strip()
        article_input["image"] = image

    if mode == "publish_now":
        article_input["isPublished"] = True
        article_input["publishDate"] = datetime.now(timezone.utc).isoformat()
    else:
        article_input["isPublished"] = False

    _attach_seo_metafields_to_input(article_input, payload)
    return article_input


def build_article_update_input(
    payload: EditorialPublishingPayload,
    *,
    mode: EditorialPublishMode,
) -> dict[str, Any]:
    from datetime import datetime, timezone

    author = payload.author.strip()
    if not author:
        raise ValueError("Autore obbligatorio per Shopify articleUpdate.")

    article_input: dict[str, Any] = {
        "title": payload.title.strip(),
        "body": payload.body_html.strip(),
        "author": {"name": author},
    }
    if payload.handle.strip():
        article_input["handle"] = payload.handle.strip()
    if payload.excerpt.strip():
        article_input["summary"] = payload.excerpt.strip()
    if payload.tags:
        article_input["tags"] = payload.tags
    if payload.template_suffix and payload.template_suffix.strip():
        article_input["templateSuffix"] = payload.template_suffix.strip()
    if payload.image_url and payload.image_url.strip():
        image: dict[str, str] = {"url": payload.image_url.strip()}
        if payload.image_alt and payload.image_alt.strip():
            image["altText"] = payload.image_alt.strip()
        article_input["image"] = image

    if mode == "publish_now":
        article_input["isPublished"] = True
        article_input["publishDate"] = datetime.now(timezone.utc).isoformat()
    else:
        article_input["isPublished"] = False

    _attach_seo_metafields_to_input(article_input, payload)
    return article_input


def format_handle_conflict_error(message: str) -> str | None:
    lowered = message.lower()
    if "handle" in lowered and ("already" in lowered or "taken" in lowered or "exists" in lowered):
        return HANDLE_CONFLICT_MESSAGE
    if "handle" in lowered and ("unique" in lowered or "duplicat" in lowered):
        return HANDLE_CONFLICT_MESSAGE
    return None


def format_shopify_publish_error(message: str) -> str:
    lowered = message.lower()
    if "author" in lowered and ("null" in lowered or "obbligator" in lowered):
        return "Shopify ha rifiutato l'articolo: author obbligatorio."
    if message.startswith("Errore GraphQL Shopify:"):
        detail = message.removeprefix("Errore GraphQL Shopify:").strip()
        handle_msg = format_handle_conflict_error(detail)
        if handle_msg:
            return handle_msg
        return f"Shopify ha rifiutato l'articolo: {detail}"
    handle_msg = format_handle_conflict_error(message)
    if handle_msg:
        return handle_msg
    return message


def shopify_publish_http_status(message: str, status_code: int | None = None) -> int:
    lowered = message.lower()
    if "impossibile contattare shopify" in lowered:
        return 502
    if status_code is not None and status_code >= 500:
        return 502
    if "errore graphql shopify" in lowered or "invalid value" in lowered:
        return 422
    if status_code in (400, 401, 403, 404, 422):
        return 422
    return 502
