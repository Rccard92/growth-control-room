"""Growth Audit Shopify commerce analysis service."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_audit import GrowthAuditFinding, GrowthAuditPage, GrowthAuditRun
from app.services.growth_audit.exceptions import (
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.run_service import (
    _ACTIVE_RUN_STATUSES,
    create_growth_audit_event,
    get_growth_audit_run,
    list_growth_audit_pages,
)
from app.services.shopify.client import ShopifyAPIError
from app.services.shopify.connect import get_shopify_client_for_store, get_shopify_store_for_project
from app.services.shopify.exceptions import (
    ShopifyCommerceApiError,
    ShopifyIntegrationNotConnectedError,
)
from app.services.shopify.scopes import assert_commerce_scopes_granted
from app.services.shopify.shopify_commerce_client import (
    fetch_shopify_orders_for_product_performance,
    fetch_shopify_products_inventory_snapshot,
)

logger = logging.getLogger(__name__)

MAX_COMMERCE_FINDINGS = 10
HIGH_SALES_THRESHOLD = Decimal("100")
HIGH_IMPRESSIONS_THRESHOLD = 200
HIGH_SESSIONS_THRESHOLD = 50
LOW_STOCK_THRESHOLD = 10


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _is_product_page(page: GrowthAuditPage) -> bool:
    page_type = (page.page_type or "").lower()
    source_type = (page.source_entity_type or "").lower()
    return page_type == "product" or source_type == "shopify_product"


def _filter_product_pages(pages: list[GrowthAuditPage]) -> list[GrowthAuditPage]:
    return [
        page
        for page in pages
        if _is_product_page(page) and (page.source_entity_gid or "").strip()
    ]


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _get_page_gsc_impressions(page: GrowthAuditPage) -> int:
    meta = (page.page_metadata or {}).get("searchConsole") or {}
    if not isinstance(meta, dict):
        return 0
    return int(meta.get("impressions") or 0)


def _get_page_ga4_sessions(page: GrowthAuditPage) -> int:
    meta = (page.page_metadata or {}).get("analytics") or {}
    if not isinstance(meta, dict):
        return 0
    return int(meta.get("sessions") or 0)


def _page_has_open_critical_findings(page: GrowthAuditPage, findings: list[GrowthAuditFinding]) -> bool:
    for finding in findings:
        if finding.page_id != page.id or finding.status != "open":
            continue
        if finding.severity in {"critical", "high"}:
            return True
    return False


def _build_page_commerce_metadata(
    *,
    period_days: int,
    product_gid: str,
    aggregates: dict[str, Any],
    snapshot: dict[str, Any] | None,
    currency: str | None,
    synced_at: str,
) -> dict[str, Any]:
    agg = aggregates.get(product_gid) or {}
    quantity_sold = int(agg.get("quantitySold") or 0)
    orders_count = int(agg.get("ordersCount") or 0)
    sales = _safe_float(agg.get("sales"))

    metadata: dict[str, Any] = {
        "periodDays": period_days,
        "quantitySold": quantity_sold,
        "ordersCount": orders_count,
        "sales": sales,
        "currency": currency or snapshot.get("currency") if snapshot else currency,
        "syncedAt": synced_at,
    }

    if quantity_sold > 0:
        metadata["averageUnitPrice"] = round(sales / quantity_sold, 2)
    if orders_count > 0:
        metadata["averageOrderValue"] = round(sales / orders_count, 2)

    if snapshot:
        metadata.update(
            {
                "stock": snapshot.get("stock"),
                "availableForSale": snapshot.get("availableForSale"),
                "productStatus": snapshot.get("status"),
                "priceMin": snapshot.get("priceMin"),
                "priceMax": snapshot.get("priceMax"),
            }
        )

    return metadata


def _compute_run_commerce_summary(
    product_pages: list[GrowthAuditPage],
    *,
    period_days: int,
    synced_at: str,
    currency: str | None,
) -> dict[str, Any]:
    total_sales = 0.0
    total_quantity = 0
    products_with_sales = 0
    products_without_sales = 0
    products_out_of_stock = 0
    top_candidates: list[tuple[float, dict[str, Any]]] = []

    for page in product_pages:
        commerce = (page.page_metadata or {}).get("shopifyCommerce") or {}
        if not isinstance(commerce, dict):
            continue
        sales = _safe_float(commerce.get("sales"))
        quantity = int(commerce.get("quantitySold") or 0)
        orders_count = int(commerce.get("ordersCount") or 0)
        stock = commerce.get("stock")
        available = commerce.get("availableForSale")

        total_sales += sales
        total_quantity += quantity
        if sales > 0 or quantity > 0:
            products_with_sales += 1
        else:
            products_without_sales += 1

        if stock is not None and int(stock) <= 0:
            products_out_of_stock += 1
        elif available is False:
            products_out_of_stock += 1

        if sales > 0 or quantity > 0:
            top_candidates.append(
                (
                    sales,
                    {
                        "pageId": str(page.id),
                        "productGid": page.source_entity_gid,
                        "title": page.source_entity_title or page.title,
                        "sales": sales,
                        "quantitySold": quantity,
                        "ordersCount": orders_count,
                    },
                )
            )

    top_candidates.sort(key=lambda item: item[0], reverse=True)

    return {
        "periodDays": period_days,
        "totalSales": round(total_sales, 2),
        "totalQuantitySold": total_quantity,
        "productsWithSales": products_with_sales,
        "productsWithoutSales": products_without_sales,
        "productsOutOfStock": products_out_of_stock,
        "currency": currency,
        "topProducts": [item[1] for item in top_candidates[:10]],
        "lastSyncedAt": synced_at,
    }


def _build_shopify_commerce_findings(
    product_pages: list[GrowthAuditPage],
    open_findings: list[GrowthAuditFinding],
) -> list[dict[str, Any]]:
    candidates: list[tuple[int, dict[str, Any]]] = []

    for page in product_pages:
        commerce = (page.page_metadata or {}).get("shopifyCommerce") or {}
        if not isinstance(commerce, dict):
            continue

        sales = _safe_float(commerce.get("sales"))
        quantity = int(commerce.get("quantitySold") or 0)
        stock = commerce.get("stock")
        available = commerce.get("availableForSale")
        gsc_impressions = _get_page_gsc_impressions(page)
        ga4_sessions = _get_page_ga4_sessions(page)
        has_critical = _page_has_open_critical_findings(page, open_findings)

        if sales >= float(HIGH_SALES_THRESHOLD) and has_critical:
            candidates.append(
                (
                    int(sales),
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "high",
                        "priority": "high",
                        "title": "Prodotto che vende con criticità aperte",
                        "description": (
                            f"Shopify mostra {sales:.2f} di vendite nel periodo "
                            f"con problemi SEO/CRO ancora aperti."
                        ),
                        "recommendation": (
                            "Prioritizza fix su title, trust, performance e disponibilità "
                            "per amplificare un prodotto già monetizzato."
                        ),
                        "how_to_validate": "Confronta revenue Shopify e conversioni nei prossimi 30 giorni.",
                        "owner_type": "cro",
                    },
                )
            )

        if (gsc_impressions >= HIGH_IMPRESSIONS_THRESHOLD or ga4_sessions >= HIGH_SESSIONS_THRESHOLD) and sales == 0 and quantity == 0:
            candidates.append(
                (
                    gsc_impressions + ga4_sessions,
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "high",
                        "priority": "high",
                        "title": "Traffico senza vendite Shopify",
                        "description": (
                            f"La pagina ha {gsc_impressions} impression GSC e "
                            f"{ga4_sessions} sessioni GA4 ma zero vendite Shopify nel periodo."
                        ),
                        "recommendation": (
                            "Rafforza offerta, trust, CTA, prezzo e disponibilità per monetizzare la domanda."
                        ),
                        "how_to_validate": "Monitora vendite Shopify e conversioni GA4 dopo gli interventi.",
                        "owner_type": "cro",
                    },
                )
            )

        stock_value = int(stock) if stock is not None else None
        if (sales > 0 or gsc_impressions >= HIGH_IMPRESSIONS_THRESHOLD) and (
            stock_value is not None and stock_value <= 0 or available is False
        ):
            candidates.append(
                (
                    int(sales) + 100,
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "high",
                        "priority": "high",
                        "title": "Prodotto con domanda ma disponibilità limitata",
                        "description": (
                            "Il prodotto ha vendite o visibilità ma risulta out of stock "
                            "o non disponibile."
                        ),
                        "recommendation": (
                            "Ripristina stock e disponibilità su Shopify prima di spingere traffico."
                        ),
                        "how_to_validate": "Verifica stock e vendite dopo il ripristino inventario.",
                        "owner_type": "cro",
                    },
                )
            )

        if sales >= float(HIGH_SALES_THRESHOLD) and stock_value is not None and 0 < stock_value <= LOW_STOCK_THRESHOLD:
            candidates.append(
                (
                    int(sales),
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "medium",
                        "priority": "medium",
                        "title": "Prodotto venditore con stock basso",
                        "description": (
                            f"Vendite {sales:.2f} nel periodo con stock residuo {stock_value}."
                        ),
                        "recommendation": "Rifornisci inventario per non perdere conversioni in arrivo.",
                        "how_to_validate": "Controlla stock e vendite dopo il rifornimento.",
                        "owner_type": "cro",
                    },
                )
            )

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in candidates[:MAX_COMMERCE_FINDINGS]]


async def analyze_growth_audit_shopify_commerce(
    session: AsyncSession,
    *,
    project_id: UUID,
    run_id: UUID,
    days: int = 30,
) -> dict[str, Any]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")

    if run.status in _ACTIVE_RUN_STATUSES:
        raise GrowthAuditValidationError(
            "Impossibile sincronizzare Shopify Commerce mentre il run è ancora in corso."
        )

    store = await get_shopify_store_for_project(project_id, session)
    if store is None or store.connection_status != "connected":
        raise ShopifyIntegrationNotConnectedError(
            "Collega Shopify per importare vendite e revenue prodotto."
        )

    client = await get_shopify_client_for_store(store)
    await assert_commerce_scopes_granted(store, session)

    pages = await list_growth_audit_pages(session, project_id, run_id)
    product_pages = _filter_product_pages(pages)
    if not product_pages:
        raise GrowthAuditValidationError(
            "Nessuna pagina prodotto collegata a Shopify in questa run."
        )

    normalized_days = max(7, min(days, 90))
    if normalized_days not in {7, 30, 90}:
        normalized_days = 30 if normalized_days > 30 else (7 if normalized_days < 15 else 30)

    end_date = date.today()
    start_date = end_date - timedelta(days=normalized_days - 1)

    logger.info(
        "Starting Shopify commerce analysis project_id=%s run_id=%s days=%s",
        project_id,
        run_id,
        normalized_days,
    )

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="shopify_commerce_analysis_started",
        phase="shopify_commerce",
        message="Sincronizzazione vendite Shopify avviata",
        progress_percent=run.progress_percent,
        payload={"days": normalized_days},
    )
    await session.flush()

    shop_domain = client.shop_domain
    access_token = client.access_token

    try:
        orders_result = await fetch_shopify_orders_for_product_performance(
            shop_domain=shop_domain,
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
        )
        product_gids = [page.source_entity_gid for page in product_pages if page.source_entity_gid]
        inventory_result = await fetch_shopify_products_inventory_snapshot(
            shop_domain=shop_domain,
            access_token=access_token,
            product_gids=product_gids,
        )
    except ShopifyCommerceApiError as exc:
        raise ShopifyCommerceApiError(str(exc), status_code=exc.status_code) from exc
    except ShopifyAPIError as exc:
        raise ShopifyCommerceApiError(str(exc), status_code=exc.status_code) from exc

    aggregates = orders_result.get("aggregates_by_product_gid") or {}
    currency = orders_result.get("currency")
    snapshots = inventory_result.get("products_by_gid") or {}
    synced_at = _utcnow().isoformat()
    pages_updated = 0

    for page in product_pages:
        product_gid = page.source_entity_gid or ""
        snapshot = snapshots.get(product_gid)
        commerce_meta = _build_page_commerce_metadata(
            period_days=normalized_days,
            product_gid=product_gid,
            aggregates=aggregates,
            snapshot=snapshot,
            currency=currency,
            synced_at=synced_at,
        )
        page.page_metadata = {
            **(page.page_metadata or {}),
            "shopifyCommerce": commerce_meta,
        }
        pages_updated += 1
        session.add(page)

    summary = _compute_run_commerce_summary(
        product_pages,
        period_days=normalized_days,
        synced_at=synced_at,
        currency=currency,
    )
    existing_summary = dict(run.summary or {})
    run.summary = {**existing_summary, "shopifyCommerce": summary}

    from sqlalchemy import select

    findings_result = await session.execute(
        select(GrowthAuditFinding).where(
            GrowthAuditFinding.run_id == run.id,
            GrowthAuditFinding.project_id == project_id,
            GrowthAuditFinding.status == "open",
        )
    )
    open_findings = list(findings_result.scalars().all())
    finding_specs = _build_shopify_commerce_findings(product_pages, open_findings)
    findings_created = 0
    for spec in finding_specs:
        finding = GrowthAuditFinding(
            run_id=run.id,
            page_id=spec["page_id"],
            project_id=project_id,
            category=spec["category"],
            severity=spec["severity"],
            priority=spec["priority"],
            title=spec["title"],
            description=spec.get("description"),
            recommendation=spec.get("recommendation"),
            how_to_validate=spec.get("how_to_validate"),
            status="open",
            finding_metadata={"source": "shopify_commerce"},
        )
        session.add(finding)
        findings_created += 1

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="shopify_commerce_analysis_completed",
        phase="shopify_commerce",
        message=(
            f"Dati ecommerce Shopify aggiornati: {summary['productsWithSales']} prodotti con vendite."
        ),
        progress_percent=run.progress_percent,
        payload={
            "pagesUpdated": pages_updated,
            "findingsCreated": findings_created,
            "summary": summary,
        },
    )

    session.add(run)
    await session.commit()
    await session.refresh(run)

    return {
        "run": run,
        "summary": summary,
        "pages_updated": pages_updated,
        "findings_created": findings_created,
        "message": "Dati ecommerce Shopify aggiornati",
    }
