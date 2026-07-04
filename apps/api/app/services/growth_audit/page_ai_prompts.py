"""Prompt builders for Growth Audit page-level AI/GEO/CRO analysis."""

from __future__ import annotations

import json
from typing import Any

from app.services.growth_audit.page_ai_output_schema import get_output_schema_instruction

_PAGE_TYPE_METHODOLOGY: dict[str, str] = {
    "product": (
        "Metodologia prodotto ecommerce: SEO on-page, schema Product, trust e rassicurazioni, "
        "chiarezza offerta, above the fold, CTA, obiezioni d'acquisto, immagini e alt, "
        "spedizione/resi/pagamento se presenti, CRO euristico, ads readiness, GEO/AI citability."
    ),
    "collection": (
        "Metodologia collection: intent commerciale, testo categoria, linking interno, "
        "filtri/UX catalogo, schema Breadcrumb/ItemList, posizionamento keyword, "
        "CRO catalogo euristico, GEO."
    ),
    "blog_article": (
        "Metodologia articolo blog: search intent, E-E-A-T, struttura H2/H3, completezza contenuto, "
        "linking interno verso prodotti, FAQ/schema, GEO/citability, CTA verso prodotto/lead."
    ),
    "blog": (
        "Metodologia blog: search intent, E-E-A-T, struttura contenuto, linking interno, GEO."
    ),
    "article": (
        "Metodologia articolo: search intent, E-E-A-T, struttura H2/H3, completezza, linking, GEO."
    ),
    "homepage": (
        "Metodologia homepage: value proposition, brand positioning, trust, navigazione, "
        "link verso categorie/prodotti, entity SEO, CRO euristico, GEO."
    ),
    "landing_page": (
        "Metodologia landing: messaggio above the fold, coerenza ads, CTA, social proof, "
        "friction points, CRO euristico, SEO/GEO base. Performance solo se dati disponibili."
    ),
    "page": (
        "Metodologia landing/static: messaggio, CTA, trust, SEO/GEO base, CRO euristico."
    ),
    "static_page": (
        "Metodologia pagina statica: chiarezza contenuto, trust, schema appropriato, linking, GEO base."
    ),
}

_DEFAULT_METHODOLOGY = (
    "Metodologia generica: SEO on-page, contenuto, trust, linking interno, CRO euristico, GEO base."
)


def _truncate_text(value: Any, max_len: int = 1200) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def build_system_prompt(
    page_type: str,
    *,
    include_seo: bool,
    include_geo: bool,
    include_cro: bool,
    include_ads_readiness: bool,
    depth: str,
) -> str:
    methodology = _PAGE_TYPE_METHODOLOGY.get(page_type, _DEFAULT_METHODOLOGY)
    areas: list[str] = []
    if include_seo:
        areas.append("SEO avanzata on-page e contenuto")
    if include_geo:
        areas.append("GEO / AI Search citability")
    if include_cro:
        areas.append("CRO / persuasione euristica (NON heatmap o session recording reali)")
    if include_ads_readiness:
        areas.append("Ads readiness e coerenza messaggio landing")
    areas_text = ", ".join(areas) if areas else "nessuna area selezionata"

    depth_note = (
        "Analisi approfondita: più findings actionable e checklist dettagliate."
        if depth == "deep"
        else "Analisi standard: findings prioritari e task operativi."
    )

    return (
        "Sei un consulente Growth Audit per ecommerce Shopify. "
        "Analizza UNA singola pagina usando solo i dati forniti. "
        "Non inventare metriche comportamentali, heatmap o dati analytics non presenti. "
        "CRO e neuromarketing devono essere euristici e basati su segnali pagina.\n\n"
        f"Tipo pagina: {page_type}\n"
        f"{methodology}\n\n"
        f"Aree richieste: {areas_text}\n"
        f"{depth_note}\n\n"
        f"{get_output_schema_instruction()}"
    )


def build_user_prompt(context: dict[str, Any]) -> str:
    safe_context = dict(context)
    if safe_context.get("shopifyEntity"):
        entity = dict(safe_context["shopifyEntity"])
        if entity.get("descriptionText"):
            entity["descriptionText"] = _truncate_text(entity["descriptionText"], 800)
        if entity.get("descriptionHtml"):
            entity["descriptionHtml"] = _truncate_text(entity["descriptionHtml"], 400)
        safe_context["shopifyEntity"] = entity
    return (
        "Analizza questa pagina Growth Audit e restituisci JSON strutturato.\n\n"
        f"CONTESTO:\n{json.dumps(safe_context, ensure_ascii=False, indent=2)}"
    )
