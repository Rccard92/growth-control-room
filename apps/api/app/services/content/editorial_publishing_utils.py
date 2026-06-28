"""Build and validate editorial publishing payloads for Shopify."""

from __future__ import annotations

import re
from typing import Any

from app.schemas.content_seo_editorial import (
    EditorialArticlePayload,
    EditorialPublishingPayload,
    EditorialPublishMode,
)

_GID_NUMERIC_RE = re.compile(r"/(\d+)$")


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
    author = (article.author_name or "").strip()
    return EditorialPublishingPayload(
        title=article.title.strip(),
        handle=article.handle.strip(),
        body_html=article.body_html.strip(),
        excerpt=article.excerpt.strip(),
        seo_title=article.seo_title.strip() or article.title.strip(),
        meta_description=article.meta_description.strip(),
        author=author,
        blog_id=default_blog_id,
        blog_gid=default_blog_gid,
        tags=list(article.tags or []),
        mode="draft",
        is_published=False,
        publish_date=None,
    )


def merge_article_into_publishing(
    existing: EditorialPublishingPayload | dict[str, Any],
    article: EditorialArticlePayload | dict[str, Any],
    *,
    overwrite: bool = False,
) -> EditorialPublishingPayload:
    base = (
        normalize_publishing_payload(existing)
        if isinstance(existing, dict)
        else existing
    )
    built = build_publishing_payload_from_article(article)
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


def validate_publishing_payload(
    payload: EditorialPublishingPayload | dict[str, Any],
    *,
    for_publish: bool = False,
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
    if for_publish and normalized.mode == "schedule":
        errors.append("La pubblicazione programmata non è ancora disponibile.")
    return errors


def build_article_create_input(
    payload: EditorialPublishingPayload,
    *,
    blog_gid: str,
    mode: EditorialPublishMode,
) -> dict[str, Any]:
    from datetime import datetime, timezone

    article_input: dict[str, Any] = {
        "blogId": blog_gid,
        "title": payload.title.strip(),
        "body": payload.body_html.strip(),
    }
    if payload.handle.strip():
        article_input["handle"] = payload.handle.strip()
    if payload.excerpt.strip():
        article_input["summary"] = payload.excerpt.strip()
    if payload.tags:
        article_input["tags"] = payload.tags
    if payload.author.strip():
        article_input["author"] = {"name": payload.author.strip()}
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

    return article_input
