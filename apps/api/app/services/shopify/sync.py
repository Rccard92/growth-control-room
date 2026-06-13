import logging
import time
from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify import (
    ShopifyDailyMetric,
    ShopifyOrder,
    ShopifyOrderLineItem,
    ShopifyOrderRefund,
    ShopifyProduct,
    ShopifyProductMetafield,
    ShopifyProductVariant,
    ShopifyStore,
)
from app.services.shopify.attribution import extract_order_attribution
from app.services.shopify.client import ShopifyGraphQLClient, parse_product_metafields
from app.services.shopify.html_utils import html_to_text

logger = logging.getLogger(__name__)


def _extract_media_images(node: dict[str, Any]) -> list[dict[str, Any]] | None:
    media_nodes = (node.get("media") or {}).get("nodes") or []
    if not media_nodes:
        featured = node.get("featuredImage") or {}
        if featured.get("url"):
            return [
                {
                    "id": featured.get("id"),
                    "url": featured.get("url"),
                    "altText": featured.get("altText"),
                    "position": 1,
                }
            ]
        return None

    images: list[dict[str, Any]] = []
    for index, media in enumerate(media_nodes):
        preview = (media.get("preview") or {}).get("image") or {}
        images.append(
            {
                "id": media.get("id"),
                "url": preview.get("url"),
                "altText": media.get("alt") or preview.get("altText"),
                "mediaContentType": media.get("mediaContentType"),
                "position": index + 1,
            }
        )
    return images or None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _parse_decimal(value: str | int | float | None) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _money_amount(node: dict[str, Any] | None, key: str) -> tuple[Decimal, str | None]:
    block = (node or {}).get(key) or {}
    money = block.get("shopMoney") or {}
    return _parse_decimal(money.get("amount")), money.get("currencyCode")


def _variant_prices(variant_nodes: list[dict[str, Any]]) -> tuple[int | None, Decimal | None, Decimal | None]:
    prices: list[Decimal] = []
    for node in variant_nodes:
        price = node.get("price")
        if price is not None and str(price).strip() != "":
            prices.append(_parse_decimal(price))
    if not prices:
        return len(variant_nodes) or None, None, None
    return len(variant_nodes), min(prices), max(prices)


async def _upsert_product(
    session: AsyncSession,
    store_id: UUID,
    node: dict[str, Any],
) -> ShopifyProduct:
    gid = node["id"]
    result = await session.execute(
        select(ShopifyProduct).where(
            ShopifyProduct.shopify_store_id == store_id,
            ShopifyProduct.shopify_gid == gid,
        )
    )
    product = result.scalar_one_or_none()
    featured = node.get("featuredImage") or {}
    seo = node.get("seo") or {}
    variant_nodes = (node.get("variants") or {}).get("nodes") or []
    variants_count, min_price, max_price = _variant_prices(variant_nodes)
    tags = node.get("tags")
    if tags is not None and not isinstance(tags, list):
        tags = None

    description_html = node.get("descriptionHtml")
    media_images = _extract_media_images(node)

    fields = {
        "title": node.get("title") or "",
        "handle": node.get("handle"),
        "status": node.get("status"),
        "vendor": node.get("vendor"),
        "product_type": node.get("productType"),
        "total_inventory": node.get("totalInventory"),
        "featured_image_url": featured.get("url"),
        "seo_title": seo.get("title"),
        "seo_description": seo.get("description"),
        "description_html": description_html,
        "description_text": html_to_text(description_html),
        "media_images": media_images,
        "tags": tags,
        "created_at_shopify": _parse_datetime(node.get("createdAt")),
        "updated_at_shopify": _parse_datetime(node.get("updatedAt")),
        "variants_count": variants_count,
        "min_price": min_price,
        "max_price": max_price,
        "raw_payload": node,
    }

    if product is None:
        product = ShopifyProduct(
            shopify_store_id=store_id,
            shopify_gid=gid,
            **fields,
        )
        session.add(product)
    else:
        for key, val in fields.items():
            setattr(product, key, val)

    await session.flush()
    await _upsert_product_metafields(session, store_id, product.id, node)
    return product


async def _upsert_product_metafields(
    session: AsyncSession,
    store_id: UUID,
    product_id: UUID,
    node: dict[str, Any],
) -> int:
    metafield_nodes = parse_product_metafields(node)
    synced_gids: set[str] = set()
    count = 0

    for mf_node in metafield_nodes:
        gid = mf_node["id"]
        synced_gids.add(gid)
        definition = mf_node.get("definition") or {}
        fields = {
            "namespace": mf_node["namespace"],
            "key": mf_node["key"],
            "type": mf_node["type"],
            "value": mf_node.get("value"),
            "definition_name": definition.get("name"),
            "definition_description": definition.get("description"),
            "raw_payload": mf_node.get("raw") or mf_node,
        }

        result = await session.execute(
            select(ShopifyProductMetafield).where(
                ShopifyProductMetafield.shopify_store_id == store_id,
                ShopifyProductMetafield.shopify_metafield_gid == gid,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            session.add(
                ShopifyProductMetafield(
                    shopify_store_id=store_id,
                    product_id=product_id,
                    shopify_metafield_gid=gid,
                    **fields,
                )
            )
        else:
            row.product_id = product_id
            for key, val in fields.items():
                setattr(row, key, val)
        count += 1

    if synced_gids:
        await session.execute(
            delete(ShopifyProductMetafield).where(
                ShopifyProductMetafield.shopify_store_id == store_id,
                ShopifyProductMetafield.product_id == product_id,
                ShopifyProductMetafield.shopify_metafield_gid.notin_(synced_gids),
            )
        )
    else:
        await session.execute(
            delete(ShopifyProductMetafield).where(
                ShopifyProductMetafield.shopify_store_id == store_id,
                ShopifyProductMetafield.product_id == product_id,
            )
        )

    await session.flush()
    return count


async def _upsert_variants(
    session: AsyncSession,
    store_id: UUID,
    product: ShopifyProduct,
    node: dict[str, Any],
) -> int:
    variant_nodes = (node.get("variants") or {}).get("nodes") or []
    synced_gids: set[str] = set()

    for variant_node in variant_nodes:
        gid = variant_node.get("id")
        if not gid:
            continue
        synced_gids.add(gid)

        result = await session.execute(
            select(ShopifyProductVariant).where(
                ShopifyProductVariant.shopify_store_id == store_id,
                ShopifyProductVariant.shopify_variant_gid == gid,
            )
        )
        variant = result.scalar_one_or_none()
        selected_options = variant_node.get("selectedOptions")
        if selected_options is not None and not isinstance(selected_options, list):
            selected_options = None

        fields = {
            "product_id": product.id,
            "title": variant_node.get("title") or "",
            "sku": variant_node.get("sku"),
            "price": _parse_decimal(variant_node.get("price"))
            if variant_node.get("price") is not None
            else None,
            "compare_at_price": _parse_decimal(variant_node.get("compareAtPrice"))
            if variant_node.get("compareAtPrice") is not None
            else None,
            "inventory_quantity": variant_node.get("inventoryQuantity"),
            "selected_options": selected_options,
            "raw_payload": variant_node,
        }

        if variant is None:
            session.add(
                ShopifyProductVariant(
                    shopify_store_id=store_id,
                    shopify_variant_gid=gid,
                    **fields,
                )
            )
        else:
            for key, val in fields.items():
                setattr(variant, key, val)

    if synced_gids:
        await session.execute(
            delete(ShopifyProductVariant).where(
                ShopifyProductVariant.product_id == product.id,
                ShopifyProductVariant.shopify_variant_gid.not_in(synced_gids),
            )
        )
    else:
        await session.execute(
            delete(ShopifyProductVariant).where(
                ShopifyProductVariant.product_id == product.id,
            )
        )

    await session.flush()
    return len(synced_gids)


async def _upsert_order(
    session: AsyncSession,
    store_id: UUID,
    node: dict[str, Any],
) -> ShopifyOrder:
    gid = node["id"]
    result = await session.execute(
        select(ShopifyOrder).where(
            ShopifyOrder.shopify_store_id == store_id,
            ShopifyOrder.shopify_gid == gid,
        )
    )
    order = result.scalar_one_or_none()

    current_total, currency = _money_amount(node, "currentTotalPriceSet")
    if current_total == 0:
        current_total, currency = _money_amount(node, "totalPriceSet")
    subtotal, _ = _money_amount(node, "currentSubtotalPriceSet")
    if subtotal == 0:
        subtotal, _ = _money_amount(node, "subtotalPriceSet")
    total_discounts, _ = _money_amount(node, "currentTotalDiscountsSet")
    shipping_price, _ = _money_amount(node, "totalShippingPriceSet")
    total_tax, _ = _money_amount(node, "currentTotalTaxSet")

    refund_nodes = (node.get("refunds") or {}).get("nodes") or []
    refund_total = Decimal("0")
    for refund_node in refund_nodes:
        amount, _ = _money_amount(refund_node, "totalRefundedSet")
        refund_total += amount
    refund_count = len(refund_nodes) if refund_nodes else None

    attribution = extract_order_attribution(node)

    fields = {
        "order_name": node.get("name"),
        "created_at_shopify": _parse_datetime(node.get("createdAt")),
        "processed_at": _parse_datetime(node.get("processedAt")),
        "financial_status": node.get("displayFinancialStatus"),
        "fulfillment_status": node.get("displayFulfillmentStatus"),
        "total_price": current_total,
        "current_total_price": current_total,
        "subtotal_price": subtotal,
        "total_discounts": total_discounts if total_discounts else None,
        "shipping_price": shipping_price if shipping_price else None,
        "total_tax": total_tax if total_tax else None,
        "refund_total": refund_total if refund_total else None,
        "refund_count": refund_count,
        "currency": currency,
        "customer_email": node.get("email"),
        "discount_codes": attribution.get("discount_codes"),
        "source_name": attribution.get("source_name"),
        "source_identifier": attribution.get("source_identifier"),
        "registered_source_url": attribution.get("registered_source_url"),
        "channel_name": attribution.get("channel_name"),
        "channel_handle": attribution.get("channel_handle"),
        "landing_page": attribution.get("landing_page"),
        "referrer_source": attribution.get("referrer_source"),
        "referrer_name": attribution.get("referrer_name"),
        "utm_source": attribution.get("utm_source"),
        "utm_medium": attribution.get("utm_medium"),
        "utm_campaign": attribution.get("utm_campaign"),
        "utm_content": attribution.get("utm_content"),
        "utm_term": attribution.get("utm_term"),
        "first_utm_source": attribution.get("first_utm_source"),
        "first_utm_medium": attribution.get("first_utm_medium"),
        "first_utm_campaign": attribution.get("first_utm_campaign"),
        "first_utm_content": attribution.get("first_utm_content"),
        "first_utm_term": attribution.get("first_utm_term"),
        "first_landing_page": attribution.get("first_landing_page"),
        "first_referral_code": attribution.get("first_referral_code"),
        "first_source": attribution.get("first_source"),
        "first_source_type": attribution.get("first_source_type"),
        "attribution_ready": attribution.get("attribution_ready"),
        "days_to_conversion": attribution.get("days_to_conversion"),
        "customer_order_index": attribution.get("customer_order_index"),
        "customer_type": attribution.get("customer_type"),
        "raw_payload": node,
    }

    if order is None:
        order = ShopifyOrder(
            shopify_store_id=store_id,
            shopify_gid=gid,
            **fields,
        )
        session.add(order)
    else:
        for key, val in fields.items():
            setattr(order, key, val)

    await session.flush()
    return order


async def _replace_line_items(
    session: AsyncSession,
    store_id: UUID,
    order: ShopifyOrder,
    node: dict[str, Any],
) -> int:
    await session.execute(
        delete(ShopifyOrderLineItem).where(ShopifyOrderLineItem.order_id == order.id)
    )

    line_item_nodes = (node.get("lineItems") or {}).get("nodes") or []
    count = 0

    for item_node in line_item_nodes:
        gid = item_node.get("id")
        if not gid:
            continue

        product = item_node.get("product") or {}
        variant = item_node.get("variant") or {}
        original_total, currency = _money_amount(item_node, "originalTotalSet")
        discounted_total, disc_currency = _money_amount(item_node, "discountedTotalSet")
        if not currency:
            currency = disc_currency

        qty = int(item_node.get("quantity") or 0)
        unit_price = original_total / qty if qty > 0 and original_total else None
        line_revenue = discounted_total if discounted_total else original_total

        session.add(
            ShopifyOrderLineItem(
                shopify_store_id=store_id,
                order_id=order.id,
                shopify_line_item_gid=gid,
                product_gid=product.get("id"),
                variant_gid=variant.get("id"),
                title=product.get("title") or item_node.get("title") or "Unknown",
                sku=item_node.get("sku") or variant.get("sku"),
                vendor=product.get("vendor") or item_node.get("vendor"),
                product_type=product.get("productType"),
                quantity=qty,
                unit_price=unit_price,
                original_total=original_total if original_total else None,
                discounted_total=line_revenue if line_revenue else None,
                currency=currency,
                raw_payload=item_node,
            )
        )
        count += 1

    await session.flush()
    return count


async def _replace_refunds(
    session: AsyncSession,
    store_id: UUID,
    order: ShopifyOrder,
    node: dict[str, Any],
) -> int:
    await session.execute(
        delete(ShopifyOrderRefund).where(ShopifyOrderRefund.order_id == order.id)
    )

    refund_nodes = (node.get("refunds") or {}).get("nodes") or []
    count = 0

    for refund_node in refund_nodes:
        gid = refund_node.get("id")
        if not gid:
            continue

        amount, currency = _money_amount(refund_node, "totalRefundedSet")
        session.add(
            ShopifyOrderRefund(
                shopify_store_id=store_id,
                order_id=order.id,
                shopify_refund_gid=gid,
                refund_created_at=_parse_datetime(refund_node.get("createdAt")),
                amount=amount,
                currency=currency,
                raw_payload=refund_node,
            )
        )
        count += 1

    await session.flush()
    return count


async def _rebuild_daily_metrics(
    session: AsyncSession,
    store: ShopifyStore,
) -> int:
    result = await session.execute(
        select(ShopifyOrder).where(ShopifyOrder.shopify_store_id == store.id)
    )
    orders = list(result.scalars().all())

    by_date: dict[date, list[ShopifyOrder]] = defaultdict(list)
    for order in orders:
        if order.created_at_shopify is None:
            continue
        by_date[order.created_at_shopify.date()].append(order)

    metrics_count = 0
    for metric_date, day_orders in by_date.items():
        gross = sum(
            (o.current_total_price or o.total_price for o in day_orders),
            Decimal("0"),
        )
        count = len(day_orders)
        aov = gross / count if count else Decimal("0")

        metric_result = await session.execute(
            select(ShopifyDailyMetric).where(
                ShopifyDailyMetric.shopify_store_id == store.id,
                ShopifyDailyMetric.date == metric_date,
            )
        )
        metric = metric_result.scalar_one_or_none()
        if metric is None:
            session.add(
                ShopifyDailyMetric(
                    shopify_store_id=store.id,
                    date=metric_date,
                    orders_count=count,
                    gross_sales=gross,
                    net_sales=gross,
                    average_order_value=aov,
                )
            )
        else:
            metric.orders_count = count
            metric.gross_sales = gross
            metric.net_sales = gross
            metric.average_order_value = aov
        metrics_count += 1

    return metrics_count


async def sync_shopify_store(
    store: ShopifyStore,
    client: ShopifyGraphQLClient,
    session: AsyncSession,
) -> dict[str, Any]:
    started = time.monotonic()

    products = await client.fetch_all_products()
    variants_synced = 0
    for node in products:
        product = await _upsert_product(session, store.id, node)
        variants_synced += await _upsert_variants(session, store.id, product, node)

    orders = await client.fetch_all_orders()
    line_items_synced = 0
    refunds_synced = 0
    for node in orders:
        order = await _upsert_order(session, store.id, node)
        line_items_synced += await _replace_line_items(session, store.id, order, node)
        refunds_synced += await _replace_refunds(session, store.id, order, node)

    metrics_count = await _rebuild_daily_metrics(session, store)

    store.last_sync_at = datetime.now(UTC)
    store.connection_status = "connected"
    await session.flush()

    duration_seconds = round(time.monotonic() - started, 2)

    logger.info(
        "Shopify sync v2 completed store_id=%s products=%d variants=%d orders=%d "
        "line_items=%d refunds=%d metrics_days=%d duration_s=%s degraded_blocks=%s",
        store.id,
        len(products),
        variants_synced,
        len(orders),
        line_items_synced,
        refunds_synced,
        metrics_count,
        duration_seconds,
        ",".join(client.degraded_order_blocks) or "none",
    )

    return {
        "products_synced": len(products),
        "variants_synced": variants_synced,
        "orders_synced": len(orders),
        "line_items_synced": line_items_synced,
        "refunds_synced": refunds_synced,
        "metrics_synced": metrics_count,
        "duration_seconds": duration_seconds,
    }
