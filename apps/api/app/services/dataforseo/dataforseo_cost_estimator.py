"""DataForSEO cost estimation (no real API calls)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.dataforseo.constants import (
    ESTIMATE_MODE_PRESETS,
    UNIT_COST_ESTIMATES,
)
from app.services.dataforseo.dataforseo_growth_audit_context import (
    load_run_product_context,
)
from app.services.dataforseo.dataforseo_usage_service import observed_unit_costs


def _resolve_estimate_params(
    *,
    mode: str,
    product_pages_count: int | None,
    seed_queries_per_page: int | None,
    keyword_ideas_per_seed: int | None,
    serp_queries_per_page: int | None,
) -> dict[str, int]:
    preset = ESTIMATE_MODE_PRESETS.get(mode, ESTIMATE_MODE_PRESETS["single_page"])
    return {
        "product_pages_count": product_pages_count
        if product_pages_count is not None
        else int(preset["product_pages_count"] or 1),
        "seed_queries_per_page": seed_queries_per_page
        if seed_queries_per_page is not None
        else int(preset["seed_queries_per_page"] or 1),
        "keyword_ideas_per_seed": keyword_ideas_per_seed
        if keyword_ideas_per_seed is not None
        else int(preset["keyword_ideas_per_seed"] or 10),
        "serp_queries_per_page": serp_queries_per_page
        if serp_queries_per_page is not None
        else int(preset["serp_queries_per_page"] or 1),
    }


def _compute_call_counts(params: dict[str, int]) -> dict[str, int]:
    pages = params["product_pages_count"]
    seed = params["seed_queries_per_page"]
    serp = params["serp_queries_per_page"]
    return {
        "searchVolume": pages * seed,
        "keywordIdeas": pages * seed,
        "serp": pages * serp,
    }


def _resolve_unit_costs(observed: dict[str, float | None]) -> tuple[dict[str, float], bool]:
    search_volume = (
        observed.get("search_volume_batch")
        or observed.get("search_volume")
        or UNIT_COST_ESTIMATES["search_volume"]
    )
    keyword_ideas = observed.get("keyword_ideas") or UNIT_COST_ESTIMATES["keyword_ideas"]
    serp = observed.get("serp") or UNIT_COST_ESTIMATES["serp"]

    has_observed = any(
        observed.get(op) is not None
        for op in ("search_volume", "search_volume_batch", "keyword_ideas", "serp")
    )

    return {
        "search_volume": float(search_volume),
        "keyword_ideas": float(keyword_ideas),
        "serp": float(serp),
    }, has_observed


def _compute_estimated_cost(
    calls: dict[str, int],
    unit_costs: dict[str, float],
) -> float:
    return round(
        calls["searchVolume"] * unit_costs["search_volume"]
        + calls["keywordIdeas"] * unit_costs["keyword_ideas"]
        + calls["serp"] * unit_costs["serp"],
        4,
    )


def _build_budget_warnings(estimated_cost_usd: float) -> list[str]:
    warnings: list[str] = []
    if estimated_cost_usd > settings.dataforseo_single_run_limit_usd:
        warnings.append(
            f"Stima supera il limite singola run ({settings.dataforseo_single_run_limit_usd} USD)."
        )
    if estimated_cost_usd > settings.dataforseo_daily_budget_usd:
        warnings.append(
            f"Stima supera il budget giornaliero ({settings.dataforseo_daily_budget_usd} USD)."
        )
    if estimated_cost_usd > settings.dataforseo_monthly_budget_usd:
        warnings.append(
            f"Stima supera il budget mensile ({settings.dataforseo_monthly_budget_usd} USD)."
        )
    return warnings


async def estimate_dataforseo_cost(
    session: AsyncSession,
    *,
    project_id: UUID,
    mode: str,
    run_id: UUID | None = None,
    product_pages_count: int | None = None,
    seed_queries_per_page: int | None = None,
    keyword_ideas_per_seed: int | None = None,
    serp_queries_per_page: int | None = None,
) -> dict[str, Any]:
    assumptions: list[str] = []
    audit_context: dict[str, Any] | None = None

    resolved = _resolve_estimate_params(
        mode=mode,
        product_pages_count=product_pages_count,
        seed_queries_per_page=seed_queries_per_page,
        keyword_ideas_per_seed=keyword_ideas_per_seed,
        serp_queries_per_page=serp_queries_per_page,
    )

    if run_id is not None:
        top_n = None
        if mode == "top_10_products":
            top_n = 10
        context = await load_run_product_context(
            session,
            run_id=run_id,
            project_id=project_id,
            top_n=top_n,
        )
        if mode == "full_site" or resolved["product_pages_count"] <= 0:
            resolved["product_pages_count"] = max(context.product_pages_count, 1)
        audit_context = {
            "productPagesCount": context.product_pages_count,
            "pagesWithGscQueries": context.pages_with_gsc_queries,
            "avgQueriesPerPage": round(context.avg_queries_per_page, 2),
        }
        assumptions.append(
            f"Run Growth Audit: {context.product_pages_count} pagine prodotto, "
            f"{context.pages_with_gsc_queries} con query GSC."
        )
        if context.avg_queries_per_page > 0:
            seed_cap = min(
                resolved["seed_queries_per_page"],
                max(int(round(context.avg_queries_per_page)), 1),
            )
            if seed_cap < resolved["seed_queries_per_page"]:
                resolved["seed_queries_per_page"] = seed_cap
                assumptions.append(
                    f"Seed query per pagina limitate a {seed_cap} in base alle query GSC medie."
                )

    observed = await observed_unit_costs(session, project_id)
    unit_costs, has_observed = _resolve_unit_costs(observed)
    calls = _compute_call_counts(resolved)
    estimated_cost = _compute_estimated_cost(calls, unit_costs)

    if has_observed:
        assumptions.append(
            "Costi unitari basati su usage log osservato per questo progetto."
        )
    else:
        assumptions.append(
            "Costi unitari conservativi di default: search volume 0.05, "
            "keyword ideas 0.10, SERP 0.10 USD."
        )

    assumptions.extend(
        [
            f"Modalità: {mode}.",
            f"Pagine prodotto considerate: {resolved['product_pages_count']}.",
            f"Seed query per pagina: {resolved['seed_queries_per_page']}.",
            f"Keyword ideas per seed (cap stimato): {resolved['keyword_ideas_per_seed']}.",
            f"SERP query per pagina: {resolved['serp_queries_per_page']}.",
            "Nessuna chiamata reale eseguita durante la stima.",
        ]
    )

    return {
        "mode": mode,
        "estimatedCalls": calls,
        "estimatedCostUsd": estimated_cost,
        "assumptions": assumptions,
        "budgetWarnings": _build_budget_warnings(estimated_cost),
        "auditContext": audit_context,
        "params": resolved,
        "estimateSource": "observed" if has_observed else "assumed",
        "observedUnitCosts": {
            "searchVolume": observed.get("search_volume_batch")
            or observed.get("search_volume"),
            "keywordIdeas": observed.get("keyword_ideas"),
            "serp": observed.get("serp"),
        },
    }
