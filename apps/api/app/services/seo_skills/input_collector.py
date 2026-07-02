"""Collect and normalize input for the future SEO Skill runtime."""

from __future__ import annotations

import ipaddress
import re
from datetime import datetime
from decimal import Decimal
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoEntityAnalysis, SeoOptimizationProposal
from app.models.shopify import ShopifyProduct, ShopifyStore
from app.services.brand_intelligence.context import BrandIntelligenceContextBuilder
from app.services.seo_skills.exceptions import (
    SkillInputCollectionError,
    UnsupportedSkillTargetError,
)
from app.services.shopify.connect import get_shopify_store_for_project

MAX_HTML_CHARS = 200_000
MAX_TEXT_CHARS = 50_000
MAX_DESCRIPTION_CHARS = 50_000
URL_FETCH_TIMEOUT_SECONDS = 15
URL_USER_AGENT = "GrowthControlRoomSeoSkillBot/1.0"
MAX_REDIRECTS = 5

_BLOCKED_SCHEMES = frozenset({"file", "ftp", "data", "javascript"})
_SKIP_TAGS = frozenset({"script", "style", "noscript"})

SUPPORTED_TARGET_TYPES = frozenset(
    {"url", "shopify_product", "shopify_collection", "domain"}
)


def is_private_or_blocked_host(hostname: str) -> bool:
    host = hostname.lower().strip().rstrip(".")
    if not host:
        return True
    if host in ("localhost", "0.0.0.0"):
        return True
    if host.endswith(".localhost"):
        return True

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # TODO: DNS resolution hardening for hostnames that resolve to private IPs.
        return False

    if ip.is_loopback or ip.is_private or ip.is_link_local:
        return True
    if ip.is_reserved or ip.is_multicast:
        return True
    if isinstance(ip, ipaddress.IPv6Address) and (
        ip in ipaddress.IPv6Network("fc00::/7")
        or ip in ipaddress.IPv6Network("fe80::/10")
    ):
        return True
    return False


def validate_public_http_url(url: str) -> str:
    normalized = url.strip()
    if not normalized:
        raise SkillInputCollectionError("url is required for target_type=url")

    parsed = urlparse(normalized)
    scheme = (parsed.scheme or "").lower()
    if scheme in _BLOCKED_SCHEMES:
        raise SkillInputCollectionError("URL host is not allowed")
    if scheme not in ("http", "https"):
        raise SkillInputCollectionError("URL host is not allowed")

    hostname = parsed.hostname
    if not hostname:
        raise SkillInputCollectionError("URL host is not allowed")
    if is_private_or_blocked_host(hostname):
        raise SkillInputCollectionError("URL host is not allowed")

    return normalized


def truncate_value(value: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(value) <= max_chars:
        return value
    if max_chars <= 3:
        return value[:max_chars]
    return value[: max_chars - 3] + "..."


class _PageMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self.meta_description: str | None = None
        self.canonical: str | None = None
        self.h1: list[str] = []
        self._text_parts: list[str] = []
        self._in_title = False
        self._in_h1 = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return

        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True
        elif tag == "meta":
            name = (attr_map.get("name") or attr_map.get("property") or "").lower()
            content = (attr_map.get("content") or "").strip()
            if content and name in ("description", "og:description") and not self.meta_description:
                self.meta_description = content
        elif tag == "link":
            rel = (attr_map.get("rel") or "").lower()
            href = (attr_map.get("href") or "").strip()
            if rel == "canonical" and href and not self.canonical:
                self.canonical = href

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth > 0:
            return
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        text = data.strip()
        if not text:
            return
        if self._in_title and not self.title:
            self.title = text
        elif self._in_h1:
            self.h1.append(text)
        else:
            self._text_parts.append(text)

    def body_text(self) -> str:
        return " ".join(self._text_parts)


def _parse_html_page(html: str) -> _PageMetadataParser:
    parser = _PageMetadataParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass
    return parser


def extract_text_from_html(html: str) -> str:
    if not html or not html.strip():
        return ""
    parsed = _parse_html_page(html)
    text = re.sub(r"\s+", " ", parsed.body_text()).strip()
    return text


def extract_page_metadata(html: str) -> dict[str, Any]:
    if not html or not html.strip():
        return {
            "title": "",
            "metaDescription": "",
            "canonical": "",
            "h1": [],
        }
    parsed = _parse_html_page(html)
    return {
        "title": parsed.title or "",
        "metaDescription": parsed.meta_description or "",
        "canonical": parsed.canonical or "",
        "h1": parsed.h1,
    }


def _empty_payload(
    *,
    project_id: UUID,
    target_type: str,
    target_id: UUID | None = None,
) -> dict[str, Any]:
    return {
        "projectId": str(project_id),
        "targetType": target_type,
        "targetId": str(target_id) if target_id else "",
        "url": "",
        "title": "",
        "html": "",
        "text": "",
        "metadata": {},
        "shopify": {},
        "brandContext": "",
        "warnings": [],
    }


def _iso_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _build_shopify_storefront_url(shop_domain: str | None, path: str) -> str | None:
    if not shop_domain or not path:
        return None
    domain = shop_domain.strip()
    if not domain:
        return None
    if domain.startswith("http://") or domain.startswith("https://"):
        base = domain.rstrip("/")
    else:
        base = f"https://{domain.rstrip('/')}"
    return f"{base}{path}"


def _seo_analysis_payload(analysis: SeoEntityAnalysis | None) -> dict[str, Any] | None:
    if analysis is None:
        return None
    return {
        "id": str(analysis.id),
        "entityType": analysis.entity_type,
        "entityId": str(analysis.entity_id),
        "entityTitle": analysis.entity_title,
        "scoreTotal": analysis.score_total,
        "severity": analysis.severity,
        "issues": analysis.issues,
        "recommendations": analysis.recommendations,
        "lastAnalyzedAt": _iso_datetime(analysis.last_analyzed_at),
    }


def _seo_proposal_payload(proposal: SeoOptimizationProposal | None) -> dict[str, Any] | None:
    if proposal is None:
        return None
    return {
        "id": str(proposal.id),
        "entityType": proposal.entity_type,
        "entityId": str(proposal.entity_id),
        "entityGid": proposal.entity_gid,
        "status": proposal.status,
        "source": proposal.source,
        "currentValues": proposal.current_values,
        "proposedValues": proposal.proposed_values,
        "reasoning": proposal.reasoning,
        "riskLevel": proposal.risk_level,
        "approvedAt": _iso_datetime(proposal.approved_at),
        "appliedAt": _iso_datetime(proposal.applied_at),
        "createdAt": _iso_datetime(proposal.created_at),
    }


async def _latest_seo_proposal(
    session: AsyncSession,
    store: ShopifyStore,
    entity_type: str,
    entity_id: UUID,
) -> SeoOptimizationProposal | None:
    result = await session.execute(
        select(SeoOptimizationProposal)
        .where(
            SeoOptimizationProposal.shopify_store_id == store.id,
            SeoOptimizationProposal.entity_type == entity_type,
            SeoOptimizationProposal.entity_id == entity_id,
        )
        .order_by(SeoOptimizationProposal.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _seo_entity_analysis(
    session: AsyncSession,
    store: ShopifyStore,
    entity_type: str,
    entity_id: UUID,
) -> SeoEntityAnalysis | None:
    result = await session.execute(
        select(SeoEntityAnalysis).where(
            SeoEntityAnalysis.shopify_store_id == store.id,
            SeoEntityAnalysis.entity_type == entity_type,
            SeoEntityAnalysis.entity_id == entity_id,
        )
    )
    return result.scalar_one_or_none()


def _product_payload(product: ShopifyProduct) -> dict[str, Any]:
    return {
        "id": str(product.id),
        "shopifyGid": product.shopify_gid,
        "title": product.title,
        "handle": product.handle,
        "vendor": product.vendor,
        "productType": product.product_type,
        "tags": product.tags or [],
        "status": product.status,
        "seoTitle": product.seo_title,
        "seoDescription": truncate_value(
            product.seo_description or "",
            MAX_DESCRIPTION_CHARS,
        )
        if product.seo_description
        else None,
        "descriptionHtml": product.description_html,
        "descriptionText": product.description_text,
        "mediaImages": product.media_images or [],
        "priceRange": {
            "minPrice": _decimal_to_float(product.min_price),
            "maxPrice": _decimal_to_float(product.max_price),
        },
        "createdAtShopify": _iso_datetime(product.created_at_shopify),
        "updatedAtShopify": _iso_datetime(product.updated_at_shopify),
    }


def _collection_payload(collection: ShopifyCollection) -> dict[str, Any]:
    return {
        "id": str(collection.id),
        "shopifyGid": collection.shopify_gid,
        "title": collection.title,
        "handle": collection.handle,
        "seoTitle": collection.seo_title,
        "seoDescription": truncate_value(
            collection.seo_description or "",
            MAX_DESCRIPTION_CHARS,
        )
        if collection.seo_description
        else None,
        "descriptionHtml": collection.description_html,
        "descriptionText": collection.description_text,
        "imageUrl": collection.image_url,
        "imageAlt": collection.image_alt,
        "productsCount": collection.products_count,
        "createdAt": _iso_datetime(collection.created_at),
        "updatedAt": _iso_datetime(collection.updated_at),
    }


async def _collect_shopify_product(
    session: AsyncSession,
    project_id: UUID,
    target_id: UUID,
) -> dict[str, Any]:
    payload = _empty_payload(
        project_id=project_id,
        target_type="shopify_product",
        target_id=target_id,
    )

    store = await get_shopify_store_for_project(project_id, session)
    if store is None:
        raise SkillInputCollectionError("Shopify store not found for this project")

    result = await session.execute(
        select(ShopifyProduct).where(
            ShopifyProduct.id == target_id,
            ShopifyProduct.shopify_store_id == store.id,
        )
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise SkillInputCollectionError("Shopify product not found for this project")

    payload["title"] = product.title or ""
    html = product.description_html or ""
    if html:
        truncated_html = truncate_value(html, MAX_HTML_CHARS)
        if len(html) > MAX_HTML_CHARS:
            payload["warnings"].append(
                f"Product description HTML truncated to {MAX_HTML_CHARS} characters."
            )
        payload["html"] = truncated_html

    text = product.description_text or extract_text_from_html(html)
    if text:
        truncated_text = truncate_value(text, MAX_TEXT_CHARS)
        if len(text) > MAX_TEXT_CHARS:
            payload["warnings"].append(
                f"Product description text truncated to {MAX_TEXT_CHARS} characters."
            )
        payload["text"] = truncated_text

    if product.handle and store.shop_domain:
        product_url = _build_shopify_storefront_url(
            store.shop_domain,
            f"/products/{product.handle}",
        )
        if product_url:
            payload["url"] = product_url
    else:
        payload["warnings"].append(
            "Could not build product URL: missing handle or shop domain."
        )

    shopify_data: dict[str, Any] = {"product": _product_payload(product)}

    try:
        analysis = await _seo_entity_analysis(session, store, "product", target_id)
        analysis_payload = _seo_analysis_payload(analysis)
        if analysis_payload:
            shopify_data["seoAnalysis"] = analysis_payload

        proposal = await _latest_seo_proposal(session, store, "product", target_id)
        proposal_payload = _seo_proposal_payload(proposal)
        if proposal_payload:
            shopify_data["latestProposal"] = proposal_payload
    except Exception:
        payload["warnings"].append(
            "Could not load existing SEO analysis or proposal for this product."
        )

    payload["shopify"] = shopify_data
    return payload


async def _collect_shopify_collection(
    session: AsyncSession,
    project_id: UUID,
    target_id: UUID,
) -> dict[str, Any]:
    payload = _empty_payload(
        project_id=project_id,
        target_type="shopify_collection",
        target_id=target_id,
    )

    store = await get_shopify_store_for_project(project_id, session)
    if store is None:
        raise SkillInputCollectionError("Shopify store not found for this project")

    result = await session.execute(
        select(ShopifyCollection).where(
            ShopifyCollection.id == target_id,
            ShopifyCollection.shopify_store_id == store.id,
        )
    )
    collection = result.scalar_one_or_none()
    if collection is None:
        raise SkillInputCollectionError("Shopify collection not found for this project")

    payload["title"] = collection.title or ""
    html = collection.description_html or ""
    if html:
        truncated_html = truncate_value(html, MAX_HTML_CHARS)
        if len(html) > MAX_HTML_CHARS:
            payload["warnings"].append(
                f"Collection description HTML truncated to {MAX_HTML_CHARS} characters."
            )
        payload["html"] = truncated_html

    text = collection.description_text or extract_text_from_html(html)
    if text:
        truncated_text = truncate_value(text, MAX_TEXT_CHARS)
        if len(text) > MAX_TEXT_CHARS:
            payload["warnings"].append(
                f"Collection description text truncated to {MAX_TEXT_CHARS} characters."
            )
        payload["text"] = truncated_text

    if collection.handle and store.shop_domain:
        collection_url = _build_shopify_storefront_url(
            store.shop_domain,
            f"/collections/{collection.handle}",
        )
        if collection_url:
            payload["url"] = collection_url
    else:
        payload["warnings"].append(
            "Could not build collection URL: missing handle or shop domain."
        )

    shopify_data: dict[str, Any] = {"collection": _collection_payload(collection)}

    try:
        analysis = await _seo_entity_analysis(session, store, "collection", target_id)
        analysis_payload = _seo_analysis_payload(analysis)
        if analysis_payload:
            shopify_data["seoAnalysis"] = analysis_payload

        proposal = await _latest_seo_proposal(session, store, "collection", target_id)
        proposal_payload = _seo_proposal_payload(proposal)
        if proposal_payload:
            shopify_data["latestProposal"] = proposal_payload
    except Exception:
        payload["warnings"].append(
            "Could not load existing SEO analysis or proposal for this collection."
        )

    payload["shopify"] = shopify_data
    return payload


async def _fetch_url_html(url: str) -> tuple[str, int, str]:
    try:
        async with httpx.AsyncClient(
            timeout=URL_FETCH_TIMEOUT_SECONDS,
            follow_redirects=True,
            max_redirects=MAX_REDIRECTS,
            headers={"User-Agent": URL_USER_AGENT},
        ) as client:
            response = await client.get(url)
    except httpx.TimeoutException as exc:
        raise SkillInputCollectionError(
            f"Timed out fetching URL after {URL_FETCH_TIMEOUT_SECONDS} seconds"
        ) from exc
    except httpx.HTTPError as exc:
        raise SkillInputCollectionError(f"Failed to fetch URL: {exc}") from exc

    html = response.text or ""
    return html, response.status_code, str(response.url)


async def _collect_url(
    session: AsyncSession,
    project_id: UUID,
    url: str,
) -> dict[str, Any]:
    del session  # URL collection does not query the database.
    validated_url = validate_public_http_url(url)
    payload = _empty_payload(project_id=project_id, target_type="url")
    payload["url"] = validated_url

    html, status_code, final_url = await _fetch_url_html(validated_url)
    if len(html) > MAX_HTML_CHARS:
        payload["warnings"].append(
            f"Fetched HTML truncated to {MAX_HTML_CHARS} characters."
        )
        html = truncate_value(html, MAX_HTML_CHARS)

    page_meta = extract_page_metadata(html)
    text = extract_text_from_html(html)
    if len(text) > MAX_TEXT_CHARS:
        payload["warnings"].append(
            f"Extracted page text truncated to {MAX_TEXT_CHARS} characters."
        )
        text = truncate_value(text, MAX_TEXT_CHARS)

    payload["title"] = page_meta.get("title") or ""
    payload["html"] = html
    payload["text"] = text
    payload["metadata"] = {
        "httpStatus": status_code,
        "finalUrl": final_url,
        "metaDescription": page_meta.get("metaDescription") or "",
        "canonical": page_meta.get("canonical") or "",
        "h1": page_meta.get("h1") or [],
    }
    return payload


def _normalize_domain_input(url_or_domain: str | None) -> tuple[str, str]:
    if not url_or_domain or not url_or_domain.strip():
        raise SkillInputCollectionError("url is required for target_type=domain")

    raw = url_or_domain.strip()
    if "://" in raw:
        parsed = urlparse(raw)
        hostname = parsed.hostname
        if not hostname:
            raise SkillInputCollectionError("Invalid domain input")
        normalized_url = f"https://{hostname}"
        return hostname.lower(), normalized_url

    host = raw.rstrip("/")
    if "/" in host:
        host = host.split("/", 1)[0]
    return host.lower(), f"https://{host}"


async def _collect_domain(
    session: AsyncSession,
    project_id: UUID,
    url: str | None,
) -> dict[str, Any]:
    del session
    domain, normalized_url = _normalize_domain_input(url)
    payload = _empty_payload(project_id=project_id, target_type="domain")
    payload["url"] = normalized_url
    payload["metadata"] = {"domain": domain}
    payload["warnings"].append(
        "Full domain crawl is not implemented yet. Only domain-level metadata was collected."
    )
    return payload


async def _attach_brand_context(
    session: AsyncSession,
    project_id: UUID,
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        brand_context = await BrandIntelligenceContextBuilder.get_prompt_context(
            session,
            project_id,
        )
    except Exception:
        brand_context = None
        payload["warnings"].append(
            "Brand context not available for this project."
        )
        return payload

    if brand_context:
        payload["brandContext"] = brand_context
    else:
        payload["warnings"].append(
            "Brand context not available for this project."
        )
    return payload


async def collect_skill_input(
    session: AsyncSession,
    project_id: UUID,
    target_type: str,
    *,
    target_id: UUID | None = None,
    url: str | None = None,
) -> dict[str, Any]:
    normalized_type = (target_type or "").strip().lower()
    if normalized_type not in SUPPORTED_TARGET_TYPES:
        raise UnsupportedSkillTargetError(
            f"Unsupported target_type: {target_type}"
        )

    if normalized_type == "shopify_product":
        if target_id is None:
            raise SkillInputCollectionError("target_id is required for shopify_product")
        payload = await _collect_shopify_product(session, project_id, target_id)
    elif normalized_type == "shopify_collection":
        if target_id is None:
            raise SkillInputCollectionError(
                "target_id is required for shopify_collection"
            )
        payload = await _collect_shopify_collection(session, project_id, target_id)
    elif normalized_type == "url":
        if not url or not url.strip():
            raise SkillInputCollectionError("url is required for target_type=url")
        payload = await _collect_url(session, project_id, url)
    else:
        payload = await _collect_domain(session, project_id, url)

    return await _attach_brand_context(session, project_id, payload)
