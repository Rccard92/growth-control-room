"""Growth Audit Merchant Center analysis service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_audit import GrowthAuditFinding, GrowthAuditPage, GrowthAuditRun
from app.models.project import Project
from app.services.google.exceptions import (
    GoogleIntegrationNotConnectedError,
    GoogleIntegrationPermissionError,
)
from app.services.google.google_tokens import get_valid_google_access_token
from app.services.google.merchant_client import fetch_merchant_products_with_issues
from app.services.growth_audit.exceptions import (
    GrowthAuditRunNotFoundError,
    GrowthAuditValidationError,
)
from app.services.growth_audit.merchant_product_matching import match_merchant_products_to_pages
from app.services.growth_audit.run_service import (
    _ACTIVE_RUN_STATUSES,
    create_growth_audit_event,
    get_growth_audit_run,
    list_growth_audit_pages,
)

logger = logging.getLogger(__name__)

MAX_MERCHANT_CENTER_FINDINGS = 10


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _is_product_page(page: GrowthAuditPage) -> bool:
    page_type = (page.page_type or "").lower()
    source_type = (page.source_entity_type or "").lower()
    return page_type == "product" or source_type == "shopify_product"


def _filter_product_pages(pages: list[GrowthAuditPage]) -> list[GrowthAuditPage]:
    return [page for page in pages if _is_product_page(page)]


def _count_critical_issues(issues: list[dict[str, Any]]) -> int:
    count = 0
    for issue in issues:
        severity = str(issue.get("severity") or "").upper()
        if severity in {"ERROR", "CRITICAL", "DISAPPROVED", "NOT_ELIGIBLE"}:
            count += 1
    return count


def _build_page_merchant_center_metadata(
    product: dict[str, Any],
    *,
    matched_by: str,
    synced_at: str,
) -> dict[str, Any]:
    issues = product.get("issues") or []
    if not isinstance(issues, list):
        issues = []
    critical_issues_count = _count_critical_issues(issues)
    return {
        "merchantProductId": product.get("merchantProductId"),
        "offerId": product.get("offerId"),
        "title": product.get("title"),
        "link": product.get("link"),
        "status": product.get("status") or "unknown",
        "availability": product.get("availability"),
        "price": product.get("price"),
        "currency": product.get("currency"),
        "brand": product.get("brand"),
        "gtin": product.get("gtin"),
        "mpn": product.get("mpn"),
        "imageLink": product.get("imageLink"),
        "destinationStatuses": product.get("destinationStatuses") or [],
        "issues": issues,
        "issuesCount": len(issues),
        "criticalIssuesCount": critical_issues_count,
        "matchedBy": matched_by,
        "syncedAt": synced_at,
    }


def _build_no_match_metadata(*, synced_at: str) -> dict[str, Any]:
    return {
        "matchedBy": "none",
        "matchStatus": "no_reliable_match",
        "syncedAt": synced_at,
    }


def _compute_run_merchant_center_summary(
    matched_pages: list[GrowthAuditPage],
    *,
    products_unmatched: int,
    synced_at: str,
) -> dict[str, Any]:
    approved = 0
    disapproved = 0
    limited = 0
    with_issues = 0
    critical_issues = 0
    issue_counter: dict[str, dict[str, Any]] = {}

    for page in matched_pages:
        meta = (page.page_metadata or {}).get("merchantCenter")
        if not isinstance(meta, dict) or meta.get("matchedBy") == "none":
            continue
        status = str(meta.get("status") or "unknown").lower()
        if status == "approved":
            approved += 1
        elif status == "disapproved":
            disapproved += 1
        elif status == "limited":
            limited += 1

        issues = meta.get("issues") or []
        if isinstance(issues, list) and issues:
            with_issues += 1
            critical_issues += int(meta.get("criticalIssuesCount") or 0)
            for issue in issues:
                if not isinstance(issue, dict):
                    continue
                code = str(issue.get("code") or "unknown")
                bucket = issue_counter.setdefault(
                    code,
                    {"code": code, "count": 0, "severity": issue.get("severity")},
                )
                bucket["count"] += 1

    top_issues = sorted(issue_counter.values(), key=lambda item: item["count"], reverse=True)[:5]

    return {
        "productsMatched": len(matched_pages),
        "productsUnmatched": products_unmatched,
        "approvedProducts": approved,
        "disapprovedProducts": disapproved,
        "limitedProducts": limited,
        "productsWithIssues": with_issues,
        "criticalIssues": critical_issues,
        "topIssues": top_issues,
        "lastSyncedAt": synced_at,
    }


def _page_has_demand(page: GrowthAuditPage) -> bool:
    metadata = page.page_metadata or {}
    shopify = metadata.get("shopifyCommerce") if isinstance(metadata.get("shopifyCommerce"), dict) else {}
    gsc = metadata.get("searchConsole") if isinstance(metadata.get("searchConsole"), dict) else {}
    analytics = metadata.get("analytics") if isinstance(metadata.get("analytics"), dict) else {}
    ga4 = metadata.get("ga4Ecommerce") if isinstance(metadata.get("ga4Ecommerce"), dict) else {}

    sales = float(shopify.get("sales") or 0)
    impressions = int(gsc.get("impressions") or 0)
    sessions = int(analytics.get("sessions") or 0)
    item_views = int(ga4.get("itemViews") or ga4.get("itemViewEvents") or 0)
    return sales > 0 or impressions >= 200 or sessions >= 50 or item_views >= 30


def _build_merchant_center_findings(
    pages: list[GrowthAuditPage],
) -> list[dict[str, Any]]:
    candidates: list[tuple[int, dict[str, Any]]] = []

    for page in pages:
        meta = (page.page_metadata or {}).get("merchantCenter")
        if not isinstance(meta, dict) or meta.get("matchedBy") == "none":
            continue

        status = str(meta.get("status") or "unknown").lower()
        issues = meta.get("issues") or []
        issues_count = int(meta.get("issuesCount") or 0)
        critical_count = int(meta.get("criticalIssuesCount") or 0)
        has_demand = _page_has_demand(page)

        if status == "disapproved" and has_demand:
            candidates.append(
                (
                    120 + critical_count * 10,
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "high",
                        "priority": "high",
                        "title": "Prodotto disapprovato su Merchant Center",
                        "description": (
                            "Il prodotto ha domanda o vendite ma risulta disapprovato nel feed Merchant Center."
                        ),
                        "recommendation": (
                            "Risolvi i problemi feed in Merchant Center per ripristinare visibilità Shopping."
                        ),
                        "how_to_validate": "Verifica stato prodotto in Merchant Center dopo la correzione.",
                        "owner_type": "cro",
                    },
                )
            )
        elif status == "limited" and has_demand:
            candidates.append(
                (
                    80 + issues_count,
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "medium",
                        "priority": "medium",
                        "title": "Prodotto limitato su Merchant Center",
                        "description": (
                            "Il prodotto ha domanda ma risulta limitato nel feed Merchant Center."
                        ),
                        "recommendation": "Controlla warning e attributi feed per sbloccare la distribuzione.",
                        "how_to_validate": "Monitora stato destinazioni dopo aggiornamento feed.",
                        "owner_type": "cro",
                    },
                )
            )
        elif issues_count > 0 and critical_count > 0 and has_demand:
            candidates.append(
                (
                    70 + critical_count * 5,
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "high" if critical_count > 0 else "medium",
                        "priority": "high" if critical_count > 0 else "medium",
                        "title": "Issue critiche Merchant Center su prodotto attivo",
                        "description": (
                            f"Merchant Center segnala {issues_count} issue, di cui {critical_count} critiche."
                        ),
                        "recommendation": "Correggi attributi prodotto (prezzo, immagini, disponibilità, identificatori).",
                        "how_to_validate": "Riesegui sync Merchant Center e verifica issue azzerate.",
                        "owner_type": "cro",
                    },
                )
            )

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in candidates[:MAX_MERCHANT_CENTER_FINDINGS]]


async def analyze_growth_audit_merchant_center(
    session: AsyncSession,
    *,
    project_id: UUID,
    run_id: UUID,
) -> dict[str, Any]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")

    if run.status in _ACTIVE_RUN_STATUSES:
        raise GrowthAuditValidationError(
            "Impossibile sincronizzare Merchant Center mentre il run è ancora in corso."
        )

    project_result = await session.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if project is None:
        raise GrowthAuditValidationError("Progetto non trovato.")

    account_id = (project.google_merchant_account_id or "").strip()
    if not account_id:
        raise GrowthAuditValidationError(
            "Seleziona un account Merchant Center nel Integration Center."
        )

    try:
        access_token = await get_valid_google_access_token(
            session,
            project_id,
            provider="merchant_center",
        )
    except GoogleIntegrationNotConnectedError as exc:
        raise GrowthAuditValidationError(str(exc)) from exc

    pages = await list_growth_audit_pages(session, project_id, run_id)
    product_pages = _filter_product_pages(pages)
    if not product_pages:
        raise GrowthAuditValidationError(
            "Nessuna pagina prodotto disponibile in questa run."
        )

    synced_at = _utcnow().isoformat()

    logger.info(
        "Starting Merchant Center analysis project_id=%s run_id=%s account_id=%s",
        project_id,
        run_id,
        account_id,
    )

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="merchant_center_analysis_started",
        phase="merchant_center",
        message="Sincronizzazione Merchant Center avviata",
        progress_percent=run.progress_percent,
        payload={"accountId": account_id},
    )
    await session.flush()

    try:
        merchant_products = await fetch_merchant_products_with_issues(
            access_token,
            account_id=account_id,
        )
    except GoogleIntegrationPermissionError:
        raise
    except Exception as exc:
        raise GrowthAuditValidationError(str(exc)) from exc

    matched_by_page, unmatched_products = match_merchant_products_to_pages(
        product_pages,
        merchant_products,
    )

    matched_page_ids = set(matched_by_page.keys())
    pages_updated = 0

    for page in product_pages:
        match_result = matched_by_page.get(page.id)
        if match_result is not None:
            merchant_meta = _build_page_merchant_center_metadata(
                match_result.product,
                matched_by=match_result.matched_by,
                synced_at=synced_at,
            )
        else:
            merchant_meta = _build_no_match_metadata(synced_at=synced_at)

        page.page_metadata = {
            **(page.page_metadata or {}),
            "merchantCenter": merchant_meta,
        }
        pages_updated += 1
        session.add(page)

    matched_pages = [page for page in product_pages if page.id in matched_page_ids]
    summary = _compute_run_merchant_center_summary(
        matched_pages,
        products_unmatched=len(unmatched_products),
        synced_at=synced_at,
    )
    existing_summary = dict(run.summary or {})
    run.summary = {**existing_summary, "merchantCenter": summary}
    session.add(run)

    finding_specs = _build_merchant_center_findings(product_pages)
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
            finding_metadata={"source": "merchant_center"},
        )
        session.add(finding)
        findings_created += 1

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="merchant_center_analysis_completed",
        phase="merchant_center",
        message="Sincronizzazione Merchant Center completata",
        progress_percent=run.progress_percent,
        payload={
            "pagesUpdated": pages_updated,
            "findingsCreated": findings_created,
            "summary": summary,
        },
    )

    await session.commit()
    await session.refresh(run)

    return {
        "run": run,
        "summary": summary,
        "pages_updated": pages_updated,
        "findings_created": findings_created,
        "message": "Dati Merchant Center aggiornati.",
    }
