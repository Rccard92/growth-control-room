"""Growth Audit Search Console analysis service."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_audit import GrowthAuditFinding, GrowthAuditPage, GrowthAuditRun
from app.services.google.google_tokens import get_valid_google_access_token
from app.services.google.search_console_client import fetch_search_console_search_analytics
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
from app.services.growth_audit.url_utils import normalize_url
from app.services.projects import get_project_in_default_workspace

logger = logging.getLogger(__name__)

MAX_GSC_FINDINGS = 10
HIGH_IMPRESSIONS_THRESHOLD = 100
LOW_CTR_THRESHOLD = 0.02
OPPORTUNITY_POSITION_MIN = 4.0
OPPORTUNITY_POSITION_MAX = 15.0
TOP_QUERIES_PER_PAGE = 5


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_gsc_page_url(url: str) -> str | None:
    try:
        return normalize_url(url)
    except Exception:
        return None


def _parse_gsc_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = row.get("keys") or []
    if not isinstance(keys, list):
        keys = []
    return {
        "keys": keys,
        "clicks": int(row.get("clicks") or 0),
        "impressions": int(row.get("impressions") or 0),
        "ctr": _safe_float(row.get("ctr")) or 0.0,
        "position": _safe_float(row.get("position")) or 0.0,
    }


def _build_page_metrics_lookup(
    page_rows: list[dict[str, Any]],
    page_query_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    metrics_by_url: dict[str, dict[str, Any]] = {}

    for row in page_rows:
        parsed = _parse_gsc_row(row)
        page_key = parsed["keys"][0] if parsed["keys"] else None
        if not isinstance(page_key, str):
            continue
        normalized = _normalize_gsc_page_url(page_key)
        if not normalized:
            continue
        metrics_by_url[normalized] = {
            "clicks": parsed["clicks"],
            "impressions": parsed["impressions"],
            "ctr": parsed["ctr"],
            "position": parsed["position"],
            "topQueries": [],
        }

    queries_by_url: dict[str, list[dict[str, Any]]] = {}
    for row in page_query_rows:
        parsed = _parse_gsc_row(row)
        if len(parsed["keys"]) < 2:
            continue
        page_key, query_key = parsed["keys"][0], parsed["keys"][1]
        if not isinstance(page_key, str) or not isinstance(query_key, str):
            continue
        normalized = _normalize_gsc_page_url(page_key)
        if not normalized:
            continue
        queries_by_url.setdefault(normalized, []).append(
            {
                "query": query_key,
                "clicks": parsed["clicks"],
                "impressions": parsed["impressions"],
                "ctr": parsed["ctr"],
                "position": parsed["position"],
            }
        )

    for normalized, queries in queries_by_url.items():
        queries.sort(key=lambda item: (item["impressions"], item["clicks"]), reverse=True)
        if normalized not in metrics_by_url:
            metrics_by_url[normalized] = {
                "clicks": sum(item["clicks"] for item in queries),
                "impressions": sum(item["impressions"] for item in queries),
                "ctr": 0.0,
                "position": 0.0,
                "topQueries": [],
            }
        metrics_by_url[normalized]["topQueries"] = queries[:TOP_QUERIES_PER_PAGE]

    for metrics in metrics_by_url.values():
        if metrics["impressions"] > 0 and metrics.get("ctr", 0) == 0:
            metrics["ctr"] = metrics["clicks"] / metrics["impressions"]

    return metrics_by_url


def _compute_run_gsc_summary(
    page_metrics: dict[str, dict[str, Any]],
    *,
    synced_at: str,
) -> dict[str, Any]:
    if not page_metrics:
        return {
            "totalClicks": 0,
            "totalImpressions": 0,
            "averageCtr": 0.0,
            "averagePosition": 0.0,
            "pagesWithData": 0,
            "opportunityPages": 0,
            "lastSyncedAt": synced_at,
        }

    total_clicks = sum(item["clicks"] for item in page_metrics.values())
    total_impressions = sum(item["impressions"] for item in page_metrics.values())
    weighted_position = sum(
        item["position"] * item["impressions"] for item in page_metrics.values()
    )
    opportunity_pages = sum(
        1
        for item in page_metrics.values()
        if item["impressions"] >= HIGH_IMPRESSIONS_THRESHOLD
        and item["ctr"] < LOW_CTR_THRESHOLD
        or (
            OPPORTUNITY_POSITION_MIN <= item["position"] <= OPPORTUNITY_POSITION_MAX
            and item["impressions"] >= 20
        )
        or (item["impressions"] > 0 and item["clicks"] == 0)
    )

    return {
        "totalClicks": total_clicks,
        "totalImpressions": total_impressions,
        "averageCtr": round(total_clicks / total_impressions, 4) if total_impressions else 0.0,
        "averagePosition": round(weighted_position / total_impressions, 2)
        if total_impressions
        else 0.0,
        "pagesWithData": len(page_metrics),
        "opportunityPages": opportunity_pages,
        "lastSyncedAt": synced_at,
    }


def _build_gsc_findings(
    pages: list[GrowthAuditPage],
    metrics_by_url: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates: list[tuple[int, dict[str, Any]]] = []

    for page in pages:
        normalized = page.normalized_url or (page.url and _normalize_gsc_page_url(page.url))
        if not normalized:
            continue
        metrics = metrics_by_url.get(normalized)
        if not metrics:
            continue

        impressions = metrics["impressions"]
        clicks = metrics["clicks"]
        ctr = metrics["ctr"]
        position = metrics["position"]
        top_queries = metrics.get("topQueries") or []

        if impressions >= HIGH_IMPRESSIONS_THRESHOLD and ctr < LOW_CTR_THRESHOLD:
            candidates.append(
                (
                    impressions,
                    {
                        "page_id": page.id,
                        "category": "search_console",
                        "severity": "high",
                        "priority": "high",
                        "title": "CTR basso con impression elevate",
                        "description": (
                            f"La pagina ha {impressions} impression e CTR {ctr:.2%} "
                            f"negli ultimi 28 giorni."
                        ),
                        "recommendation": (
                            "Ottimizza title e meta description per aumentare il CTR "
                            "sulle query già visibili."
                        ),
                        "how_to_validate": "Confronta SERP e snippet dopo le modifiche in GSC.",
                        "owner_type": "seo",
                    },
                )
            )

        if (
            OPPORTUNITY_POSITION_MIN <= position <= OPPORTUNITY_POSITION_MAX
            and impressions >= 20
        ):
            candidates.append(
                (
                    impressions,
                    {
                        "page_id": page.id,
                        "category": "seo",
                        "severity": "medium",
                        "priority": "medium",
                        "title": "Opportunità posizionamento Search Console",
                        "description": (
                            f"Posizione media {position:.1f} con {impressions} impression."
                        ),
                        "recommendation": (
                            "Rafforza contenuto e internal linking per spingere la pagina "
                            "nella top 3."
                        ),
                        "how_to_validate": "Monitora position e clicks in GSC per 2-4 settimane.",
                        "owner_type": "content",
                    },
                )
            )

        if impressions > 0 and clicks == 0:
            candidates.append(
                (
                    impressions,
                    {
                        "page_id": page.id,
                        "category": "search_console",
                        "severity": "medium",
                        "priority": "medium",
                        "title": "Impression senza click",
                        "description": (
                            f"La pagina compare in SERP ({impressions} impression) "
                            "ma non genera click."
                        ),
                        "recommendation": (
                            "Migliora title, meta e allineamento intent per aumentare i click."
                        ),
                        "how_to_validate": "Verifica CTR pagina in GSC dopo l'ottimizzazione.",
                        "owner_type": "seo",
                    },
                )
            )

        if top_queries:
            top_query = top_queries[0]
            if top_query["impressions"] >= 30 and top_query["position"] > 10:
                candidates.append(
                    (
                        top_query["impressions"],
                        {
                            "page_id": page.id,
                            "category": "seo",
                            "severity": "medium",
                            "priority": "medium",
                            "title": "Query rilevante con contenuto debole",
                            "description": (
                                f"Query «{top_query['query']}» con "
                                f"{top_query['impressions']} impression e posizione "
                                f"{top_query['position']:.1f}."
                            ),
                            "recommendation": (
                                "Allinea H1, contenuto e schema alla query principale."
                            ),
                            "how_to_validate": "Controlla ranking query in GSC dopo il refresh.",
                            "owner_type": "content",
                        },
                    )
                )

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in candidates[:MAX_GSC_FINDINGS]]


async def analyze_growth_audit_search_console(
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
            "Impossibile sincronizzare Search Console mentre il run è ancora in corso."
        )

    project = await get_project_in_default_workspace(project_id, session)
    site_url = (project.search_console_site_url or "").strip()
    if not site_url:
        raise GrowthAuditValidationError(
            "Seleziona prima una proprietà Search Console."
        )

    normalized_days = max(1, min(days, 90))
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=normalized_days - 1)

    logger.info(
        "Starting Search Console analysis project_id=%s run_id=%s site_url=%s",
        project_id,
        run_id,
        site_url,
    )

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="search_console_analysis_started",
        phase="search_console",
        message=f"Sincronizzazione Search Console avviata per {site_url}",
        progress_percent=run.progress_percent,
        payload={"siteUrl": site_url, "days": normalized_days},
    )
    await session.flush()

    access_token = await get_valid_google_access_token(
        session,
        project_id,
        provider="google_search_console",
    )

    page_analytics = await fetch_search_console_search_analytics(
        access_token,
        site_url=site_url,
        start_date=start_date,
        end_date=end_date,
        dimensions=["page"],
        row_limit=25000,
    )
    page_query_analytics = await fetch_search_console_search_analytics(
        access_token,
        site_url=site_url,
        start_date=start_date,
        end_date=end_date,
        dimensions=["page", "query"],
        row_limit=5000,
    )

    page_rows = page_analytics.get("rows") or []
    page_query_rows = page_query_analytics.get("rows") or []
    if not isinstance(page_rows, list):
        page_rows = []
    if not isinstance(page_query_rows, list):
        page_query_rows = []

    metrics_by_url = _build_page_metrics_lookup(page_rows, page_query_rows)
    pages = await list_growth_audit_pages(session, project_id, run_id)
    synced_at = _utcnow().isoformat()
    pages_updated = 0

    for page in pages:
        normalized = page.normalized_url or (page.url and _normalize_gsc_page_url(page.url))
        if not normalized:
            continue
        metrics = metrics_by_url.get(normalized)
        if not metrics:
            continue
        page.page_metadata = {
            **(page.page_metadata or {}),
            "searchConsole": {
                "clicks": metrics["clicks"],
                "impressions": metrics["impressions"],
                "ctr": metrics["ctr"],
                "position": metrics["position"],
                "topQueries": metrics.get("topQueries") or [],
                "syncedAt": synced_at,
            },
        }
        pages_updated += 1
        session.add(page)

    summary = _compute_run_gsc_summary(metrics_by_url, synced_at=synced_at)
    existing_summary = dict(run.summary or {})
    run.summary = {**existing_summary, "searchConsole": summary}

    finding_specs = _build_gsc_findings(pages, metrics_by_url)
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
            finding_metadata={"source": "search_console"},
        )
        session.add(finding)
        findings_created += 1

    await create_growth_audit_event(
        session,
        run_id=run.id,
        project_id=project_id,
        event_type="search_console_analysis_completed",
        phase="search_console",
        message=(
            f"Dati Search Console aggiornati: {summary['pagesWithData']} pagine, "
            f"{summary['totalClicks']} click."
        ),
        progress_percent=run.progress_percent,
        payload={
            "siteUrl": site_url,
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
