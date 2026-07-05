"""Growth Audit Google Analytics 4 analysis service."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.parse import urlparse, urlunparse
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_audit import GrowthAuditFinding, GrowthAuditPage, GrowthAuditRun
from app.services.google.analytics_client import fetch_ga4_landing_pages_report
from app.services.google.google_tokens import get_valid_google_access_token
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
from app.services.growth_audit.url_utils import get_url_path, normalize_url
from app.services.projects import get_project_in_default_workspace

logger = logging.getLogger(__name__)

MAX_GA4_FINDINGS = 10
HIGH_TRAFFIC_SESSIONS_THRESHOLD = 50
LOW_ENGAGEMENT_RATE_THRESHOLD = 0.4
LOW_CONVERSION_SESSIONS_THRESHOLD = 30


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _normalize_ga4_landing_path(landing: str, base_url: str) -> str | None:
    trimmed = landing.strip()
    if not trimmed:
        return None
    path_with_query = trimmed.split("?", 1)[0]
    if path_with_query.startswith("http://") or path_with_query.startswith("https://"):
        try:
            return normalize_url(path_with_query)
        except Exception:
            return None

    parsed_base = urlparse(base_url)
    if not parsed_base.scheme or not parsed_base.netloc:
        return None
    path = path_with_query if path_with_query.startswith("/") else f"/{path_with_query}"
    candidate = urlunparse(
        (
            parsed_base.scheme.lower(),
            parsed_base.netloc.lower(),
            path,
            "",
            "",
            "",
        )
    )
    try:
        return normalize_url(candidate)
    except Exception:
        return None


def _build_landing_metrics_lookup(
    rows: list[dict[str, Any]],
    *,
    base_url: str,
) -> dict[str, dict[str, Any]]:
    metrics_by_url: dict[str, dict[str, Any]] = {}

    for row in rows:
        landing = row.get("landingPagePlusQueryString")
        if not isinstance(landing, str):
            continue
        normalized = _normalize_ga4_landing_path(landing, base_url)
        if not normalized:
            continue

        sessions = _safe_int(row.get("sessions"))
        total_users = _safe_int(row.get("totalUsers"))
        engaged_sessions = _safe_int(row.get("engagedSessions"))
        engagement_rate = _safe_float(row.get("engagementRate")) or 0.0
        average_session_duration = _safe_float(row.get("averageSessionDuration")) or 0.0
        conversions = _safe_int(row.get("conversions"))
        revenue = _safe_float(row.get("totalRevenue")) or 0.0

        if normalized not in metrics_by_url:
            metrics_by_url[normalized] = {
                "sessions": 0,
                "totalUsers": 0,
                "engagedSessions": 0,
                "engagementRate": 0.0,
                "averageSessionDuration": 0.0,
                "conversions": 0,
                "revenue": 0.0,
                "_engagement_weight": 0,
            }

        entry = metrics_by_url[normalized]
        entry["sessions"] += sessions
        entry["totalUsers"] += total_users
        entry["engagedSessions"] += engaged_sessions
        entry["conversions"] += conversions
        entry["revenue"] += revenue
        if sessions > 0:
            entry["_engagement_weight"] += sessions
            entry["engagementRate"] += engagement_rate * sessions
            entry["averageSessionDuration"] += average_session_duration * sessions

    for entry in metrics_by_url.values():
        weight = entry.pop("_engagement_weight", 0)
        if weight > 0:
            entry["engagementRate"] = round(entry["engagementRate"] / weight, 4)
            entry["averageSessionDuration"] = round(entry["averageSessionDuration"] / weight, 2)
        entry["revenue"] = round(entry["revenue"], 2)

    return metrics_by_url


def _compute_run_analytics_summary(
    page_metrics: dict[str, dict[str, Any]],
    *,
    synced_at: str,
) -> dict[str, Any]:
    if not page_metrics:
        return {
            "totalSessions": 0,
            "totalUsers": 0,
            "averageEngagementRate": 0.0,
            "totalConversions": 0,
            "totalRevenue": 0.0,
            "pagesWithData": 0,
            "lowEngagementPages": 0,
            "highTrafficLowConversionPages": 0,
            "lastSyncedAt": synced_at,
        }

    total_sessions = sum(item["sessions"] for item in page_metrics.values())
    total_users = sum(item["totalUsers"] for item in page_metrics.values())
    total_conversions = sum(item["conversions"] for item in page_metrics.values())
    total_revenue = round(sum(item["revenue"] for item in page_metrics.values()), 2)
    weighted_engagement = sum(
        item["engagementRate"] * item["sessions"] for item in page_metrics.values()
    )
    low_engagement_pages = sum(
        1
        for item in page_metrics.values()
        if item["sessions"] >= HIGH_TRAFFIC_SESSIONS_THRESHOLD
        and item["engagementRate"] < LOW_ENGAGEMENT_RATE_THRESHOLD
    )
    high_traffic_low_conversion_pages = sum(
        1
        for item in page_metrics.values()
        if item["sessions"] >= LOW_CONVERSION_SESSIONS_THRESHOLD
        and item["conversions"] == 0
    )

    return {
        "totalSessions": total_sessions,
        "totalUsers": total_users,
        "averageEngagementRate": round(weighted_engagement / total_sessions, 4)
        if total_sessions
        else 0.0,
        "totalConversions": total_conversions,
        "totalRevenue": total_revenue,
        "pagesWithData": len(page_metrics),
        "lowEngagementPages": low_engagement_pages,
        "highTrafficLowConversionPages": high_traffic_low_conversion_pages,
        "lastSyncedAt": synced_at,
    }


def _build_ga4_findings(
    pages: list[GrowthAuditPage],
    metrics_by_url: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates: list[tuple[int, dict[str, Any]]] = []

    for page in pages:
        normalized = page.normalized_url
        if not normalized:
            continue
        metrics = metrics_by_url.get(normalized)
        if not metrics:
            continue

        sessions = metrics["sessions"]
        engagement_rate = metrics["engagementRate"]
        conversions = metrics["conversions"]
        revenue = metrics["revenue"]
        page_type = (page.page_type or "").lower()

        if sessions >= HIGH_TRAFFIC_SESSIONS_THRESHOLD and engagement_rate < LOW_ENGAGEMENT_RATE_THRESHOLD:
            candidates.append(
                (
                    sessions,
                    {
                        "page_id": page.id,
                        "category": "analytics",
                        "severity": "high",
                        "priority": "high",
                        "title": "Traffico elevato con engagement basso",
                        "description": (
                            f"La pagina ha {sessions} sessioni GA4 con engagement rate "
                            f"{engagement_rate:.1%}."
                        ),
                        "recommendation": (
                            "Migliora above-the-fold, velocità percepita e allineamento "
                            "intent/contenuto per aumentare l'engagement."
                        ),
                        "how_to_validate": "Confronta engagement rate GA4 dopo le modifiche.",
                        "owner_type": "cro",
                    },
                )
            )

        if sessions >= LOW_CONVERSION_SESSIONS_THRESHOLD and conversions == 0:
            owner = "cro" if page_type in ("product", "landing", "landing_page") else "content"
            candidates.append(
                (
                    sessions,
                    {
                        "page_id": page.id,
                        "category": "cro" if page_type in ("product", "landing", "landing_page") else "analytics",
                        "severity": "high" if sessions >= HIGH_TRAFFIC_SESSIONS_THRESHOLD else "medium",
                        "priority": "high" if sessions >= HIGH_TRAFFIC_SESSIONS_THRESHOLD else "medium",
                        "title": "Traffico GA4 senza conversioni",
                        "description": (
                            f"La pagina registra {sessions} sessioni ma nessuna conversione GA4."
                        ),
                        "recommendation": (
                            "Rivedi CTA, proof sociale, offerta e frizione checkout/contatto."
                        ),
                        "how_to_validate": "Monitora conversioni GA4 sulle landing dopo il fix.",
                        "owner_type": owner,
                    },
                )
            )

        if page_type == "product" and sessions >= LOW_CONVERSION_SESSIONS_THRESHOLD and revenue < 1:
            candidates.append(
                (
                    sessions,
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "medium",
                        "priority": "medium",
                        "title": "Prodotto con traffico ma pochi acquisti",
                        "description": (
                            f"Pagina prodotto con {sessions} sessioni GA4 e revenue {revenue:.2f}."
                        ),
                        "recommendation": (
                            "Ottimizza scheda prodotto: benefit, trust, varianti, CTA e contenuto commerciale."
                        ),
                        "how_to_validate": "Verifica revenue e conversioni prodotto in GA4.",
                        "owner_type": "cro",
                    },
                )
            )

        if page_type in ("landing", "landing_page") and sessions >= HIGH_TRAFFIC_SESSIONS_THRESHOLD:
            candidates.append(
                (
                    sessions,
                    {
                        "page_id": page.id,
                        "category": "cro",
                        "severity": "medium",
                        "priority": "medium",
                        "title": "Landing strategica da ottimizzare",
                        "description": (
                            f"Landing con {sessions} sessioni GA4: opportunità CRO su traffico reale."
                        ),
                        "recommendation": (
                            "Prioritizza test su headline, form, CTA e sezione proof."
                        ),
                        "how_to_validate": "Misura conversioni e scroll engagement post-test.",
                        "owner_type": "cro",
                    },
                )
            )

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in candidates[:MAX_GA4_FINDINGS]]


async def analyze_growth_audit_analytics(
    session: AsyncSession,
    *,
    project_id: UUID,
    run_id: UUID,
    days: int = 28,
) -> dict[str, Any]:
    run = await get_growth_audit_run(session, project_id, run_id)
    if run is None:
        raise GrowthAuditRunNotFoundError(f"Growth Audit run {run_id} not found")

    if run.status in _ACTIVE_RUN_STATUSES:
        raise GrowthAuditValidationError(
            "Impossibile sincronizzare GA4 mentre il run è ancora in corso."
        )

    project = await get_project_in_default_workspace(project_id, session)
    property_id = (project.google_analytics_property_id or "").strip()
    if not property_id:
        raise GrowthAuditValidationError("Seleziona prima una proprietà GA4.")

    normalized_days = max(1, min(days, 90))
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=normalized_days - 1)
    base_url = (project.public_site_url or run.root_url or "").strip()

    logger.info(
        "Starting GA4 analysis project_id=%s run_id=%s property_id=%s",
        project_id,
        run_id,
        property_id,
    )

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="analytics_analysis_started",
        phase="analytics",
        message=f"Sincronizzazione GA4 avviata per property {property_id}",
        progress_percent=run.progress_percent,
        payload={"propertyId": property_id, "days": normalized_days},
    )
    await session.flush()

    access_token = await get_valid_google_access_token(
        session,
        project_id,
        provider="ga4",
    )

    report = await fetch_ga4_landing_pages_report(
        access_token,
        property_id=property_id,
        start_date=start_date,
        end_date=end_date,
        limit=10000,
    )

    rows = report.get("rows") or []
    if not isinstance(rows, list):
        rows = []

    metrics_by_url = _build_landing_metrics_lookup(rows, base_url=base_url)
    pages = await list_growth_audit_pages(session, project_id, run_id)
    synced_at = _utcnow().isoformat()
    pages_updated = 0

    for page in pages:
        normalized = page.normalized_url
        if not normalized:
            continue
        metrics = metrics_by_url.get(normalized)
        if not metrics:
            continue
        page.page_metadata = {
            **(page.page_metadata or {}),
            "analytics": {
                "sessions": metrics["sessions"],
                "totalUsers": metrics["totalUsers"],
                "engagedSessions": metrics["engagedSessions"],
                "engagementRate": metrics["engagementRate"],
                "averageSessionDuration": metrics["averageSessionDuration"],
                "conversions": metrics["conversions"],
                "revenue": metrics["revenue"],
                "source": "ga4",
                "periodDays": normalized_days,
                "syncedAt": synced_at,
            },
        }
        pages_updated += 1
        session.add(page)

    summary = _compute_run_analytics_summary(metrics_by_url, synced_at=synced_at)
    existing_summary = dict(run.summary or {})
    run.summary = {**existing_summary, "analytics": summary}

    finding_specs = _build_ga4_findings(pages, metrics_by_url)
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
            finding_metadata={"source": "ga4"},
        )
        session.add(finding)
        findings_created += 1

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="analytics_analysis_completed",
        phase="analytics",
        message=(
            f"Dati GA4 aggiornati: {summary['pagesWithData']} pagine, "
            f"{summary['totalSessions']} sessioni."
        ),
        progress_percent=run.progress_percent,
        payload={
            "propertyId": property_id,
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
    }
