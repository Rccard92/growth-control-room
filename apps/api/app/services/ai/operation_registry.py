"""Central registry of AI operations in Growth Control Room."""

from __future__ import annotations


from typing import Literal

from pydantic import BaseModel

from app.core.config import settings

QualityLevel = Literal["low", "medium", "high", "critical"]
CostSensitivity = Literal["low", "medium", "high"]
OperationStatus = Literal["implemented", "planned", "non_ai"]
UiCategory = Literal[
    "brand_intelligence",
    "product_collection_seo",
    "blog_articles",
    "ped_social",
    "email_ads",
    "seo_advanced",
]


class AiOperationDefinition(BaseModel):
    operation_key: str
    label: str
    module: str
    operation: str
    context_profile: str
    entity_type: str | None = None
    recommended_tier: str
    recommended_model_env_key: str
    recommended_max_output_tokens: int
    recommended_temperature: float
    quality_level: QualityLevel = "medium"
    cost_sensitivity: CostSensitivity = "medium"
    description: str
    recommended_use: str
    warning_notes: str | None = None
    status: OperationStatus = "implemented"
    enabled: bool = True
    ui_category: UiCategory = "brand_intelligence"
    gcr_recommended_model: str = "gpt-5.4"
    gcr_recommendation_reason: str = ""

    model_config = {"populate_by_name": True}


def tier_cost_profile_label(tier: str) -> str:
    if tier == "cheap":
        return "profilo costo: leggero"
    if tier in ("premium", "reasoning"):
        return "profilo costo: alta qualità"
    if tier == "fallback":
        return "profilo costo: ripiego"
    return "profilo costo: bilanciato"


GCR_METADATA: dict[str, dict[str, str]] = {
    "brand_profile_enrichment": {
        "ui_category": "brand_intelligence",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Usa un modello leggero: arricchimento breve e strutturato.",
        "description": "Arricchisce il profilo brand con dati strutturati.",
    },
    "brand_identity_import": {
        "ui_category": "brand_intelligence",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Equilibrio qualità/costo per estrazione da documenti brand.",
        "description": "Importa identità e tono da file brand.",
    },
    "visual_identity_extraction": {
        "ui_category": "brand_intelligence",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Analisi visiva con contesto sufficiente senza sprechi.",
        "description": "Estrae palette e stile visivo dal brand.",
    },
    "safe_claims_import": {
        "ui_category": "brand_intelligence",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Claim sanitari richiedono accuratezza: evita modelli troppo leggeri.",
        "description": "Importa e valida safe claims da documenti.",
    },
    "product_knowledge_general_import": {
        "ui_category": "brand_intelligence",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Sintesi knowledge generale con buon rapporto qualità/costo.",
        "description": "Importa product knowledge generale.",
    },
    "product_knowledge_item_import": {
        "ui_category": "brand_intelligence",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Estrazione per prodotto con contesto medio-lungo.",
        "description": "Importa knowledge per singolo prodotto.",
    },
    "faq_objections_import": {
        "ui_category": "brand_intelligence",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Parsing FAQ strutturate con modello bilanciato.",
        "description": "Importa FAQ e obiezioni da file.",
    },
    "brand_document_extraction": {
        "ui_category": "brand_intelligence",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Estrazione fatti da PDF con qualità affidabile.",
        "description": "Estrae fatti da documenti brand.",
    },
    "brand_synthesis": {
        "ui_category": "brand_intelligence",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Sintesi moduli BI con output coerente.",
        "description": "Sintetizza sezioni Brand Intelligence.",
    },
    "brand_brief_synthesis": {
        "ui_category": "brand_intelligence",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Brief intelligence da batch con qualità narrativa media.",
        "description": "Genera brief brand da import batch.",
    },
    "product_seo_field": {
        "ui_category": "product_collection_seo",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Usa un modello leggero: singolo campo SEO breve.",
        "description": "Genera un campo SEO singolo per prodotto.",
    },
    "collection_seo_field": {
        "ui_category": "product_collection_seo",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Usa un modello leggero: meta collection brevi.",
        "description": "Genera un campo SEO singolo per collection.",
    },
    "product_image_alt": {
        "ui_category": "product_collection_seo",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Usa un modello leggero: è un task breve e controllato.",
        "description": "Genera testi ALT brevi per immagini prodotto.",
    },
    "collection_image_alt": {
        "ui_category": "product_collection_seo",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Usa un modello leggero per alt testuali brevi.",
        "description": "Genera testi ALT per immagini collection.",
    },
    "product_seo_full_proposal": {
        "ui_category": "product_collection_seo",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Proposta multi-campo con contesto brand: modello bilanciato.",
        "description": "Proposta SEO completa per prodotto.",
    },
    "collection_seo_full_proposal": {
        "ui_category": "product_collection_seo",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Proposta SEO collection con qualità e costo equilibrati.",
        "description": "Proposta SEO completa per collection.",
    },
    "seo_compliance_review": {
        "ui_category": "product_collection_seo",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Revisione compliance: non usare modelli troppo leggeri.",
        "description": "Revisione compliance SEO su contenuti.",
    },
    "editorial_plan_generation": {
        "ui_category": "blog_articles",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Funzione rule-based: nessun modello AI attivo.",
        "description": "Piano editoriale (non usa AI).",
    },
    "blog_brief_generation": {
        "ui_category": "blog_articles",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Brief strutturato con brand context: modello bilanciato.",
        "description": "Genera brief editoriale per articoli blog.",
    },
    "blog_brief_batch_item": {
        "ui_category": "blog_articles",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Stesso profilo del brief singolo in batch.",
        "description": "Genera brief in batch editoriale.",
    },
    "article_draft_generation": {
        "ui_category": "blog_articles",
        "gcr_recommended_model": "gpt-5.5",
        "gcr_recommendation_reason": "Alta qualità per articoli lunghi, tono brand e claim.",
        "description": "Genera bozza articolo completa da brief.",
    },
    "editorial_image_generation": {
        "ui_category": "blog_articles",
        "gcr_recommended_model": "gpt-image-2",
        "gcr_recommendation_reason": "Immagine hero editoriale da contesto articolo e brand.",
        "description": "Genera immagine hero per articolo editoriale.",
    },
    "editorial_image_edit": {
        "ui_category": "blog_articles",
        "gcr_recommended_model": "gpt-image-2",
        "gcr_recommendation_reason": "Rigenera immagine hero con istruzioni di modifica.",
        "description": "Modifica immagine hero editoriale.",
    },
    "article_rewrite": {
        "ui_category": "blog_articles",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Riscrittura mantiene tono brand con costo contenuto.",
        "description": "Riscrive articoli esistenti.",
    },
    "article_meta_generation": {
        "ui_category": "blog_articles",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Meta title/description brevi: modello leggero.",
        "description": "Genera meta SEO per articoli.",
    },
    "article_compliance_review": {
        "ui_category": "blog_articles",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Revisione claim su articolo: qualità affidabile.",
        "description": "Revisione compliance su articoli.",
    },
    "ped_strategy": {
        "ui_category": "ped_social",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Strategia PED richiede ragionamento strutturato.",
        "description": "Genera strategia PED.",
    },
    "ped_calendar_generation": {
        "ui_category": "ped_social",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Calendario editoriale con output medio-lungo.",
        "description": "Genera calendario contenuti PED.",
    },
    "ped_post_copy": {
        "ui_category": "ped_social",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Copy social breve: modello leggero.",
        "description": "Genera copy per post social.",
    },
    "ped_creative_prompt": {
        "ui_category": "ped_social",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Prompt creativi con variabilità controllata.",
        "description": "Genera prompt creativi PED.",
    },
    "ped_image_prompt": {
        "ui_category": "ped_social",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Prompt immagine breve: massimo risparmio.",
        "description": "Genera prompt per immagini PED.",
    },
    "social_comment_response": {
        "ui_category": "ped_social",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Risposte brevi ai commenti: modello leggero.",
        "description": "Genera risposte a commenti social.",
    },
    "seo_keyword_research": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Ricerca keyword con analisi strutturata.",
        "description": "Ricerca keyword SEO avanzata.",
    },
    "seo_content_gap_analysis": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Gap analysis con contesto medio.",
        "description": "Analisi content gap SEO.",
    },
    "seo_article_outline": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Outline articolo con struttura coerente.",
        "description": "Genera outline articoli SEO.",
    },
    "seo_article_generation": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.5",
        "gcr_recommendation_reason": "Articoli SEO lunghi: alta qualità.",
        "description": "Genera articoli SEO completi.",
    },
    "seo_article_optimization": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Ottimizzazione con revisione mirata.",
        "description": "Ottimizza articoli SEO esistenti.",
    },
    "claude_seo_audit": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Audit SEO completo con output strutturato e priorità azioni.",
        "description": "Audit SEO full-site: crawlability, indexazione, on-page e fix prioritari.",
    },
    "claude_seo_page": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Analisi pagina singola con output strutturato e contesto sufficiente.",
        "description": "Analizza una singola pagina con regole Claude SEO adattate alla Growth Control Room.",
    },
    "claude_seo_technical": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Revisione tecnica approfondita con segnali strutturati.",
        "description": "Revisione SEO tecnica: robots, canonical, redirect, indexazione e blocker.",
    },
    "claude_seo_content": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Analisi contenuto con qualità e intent di ricerca.",
        "description": "Analisi qualità contenuto, allineamento keyword, E-E-A-T e raccomandazioni editoriali.",
    },
    "claude_seo_content_brief": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Brief strutturato con outline e keyword mirate.",
        "description": "Genera brief SEO con search intent, outline, keyword e template per tipo pagina.",
    },
    "claude_seo_schema": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Structured data con JSON-LD controllato.",
        "description": "Analizza e propone miglioramenti Schema.org e JSON-LD per pagine ecommerce e contenuti.",
    },
    "claude_seo_geo": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Skill SEO avanzata: output strutturato con contesto pagina.",
        "description": "Valuta la pagina per AI Search, citabilità, chiarezza semantica ed entità.",
    },
    "claude_seo_images": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Task mirato su alt text e segnali immagine con modello standard.",
        "description": "Analizza alt text, naming, formati, peso immagini e opportunità SEO immagini.",
    },
    "claude_seo_sitemap_analyze": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Analisi sitemap con output strutturato.",
        "description": "Analizza copertura sitemap XML, orphan pages e gap di indicizzazione.",
    },
    "claude_seo_sitemap_generate": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Generazione struttura sitemap con priorità URL.",
        "description": "Propone o affina struttura sitemap XML con priorità e changefreq.",
    },
    "claude_seo_plan": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Roadmap SEO strategica con output multi-sezione.",
        "description": "Roadmap SEO strategica con iniziative prioritarie, timeline e KPI.",
    },
    "claude_seo_competitor_pages": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Analisi competitiva con confronto SERP strutturato.",
        "description": "Analizza landing competitor per gap contenuto, overlap SERP e differenziazione.",
    },
    "claude_seo_hreflang": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Audit hreflang mirato con raccomandazioni implementative.",
        "description": "Audit tag hreflang e guida implementazione per siti multilingua.",
    },
    "claude_seo_programmatic": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Strategia programmatic SEO con pattern URL e template.",
        "description": "Template programmatic SEO, pattern URL e strategie di scala per cataloghi grandi.",
    },
    "claude_seo_cluster": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Clustering keyword con architettura hub-and-spoke.",
        "description": "Clustering keyword hub-and-spoke con overlap SERP e architettura contenuti.",
    },
    "claude_seo_sxo": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Audit SXO che combina SEO e segnali UX.",
        "description": "Audit Search Experience Optimization: CTR, engagement e miglioramenti conversion-oriented.",
    },
    "claude_seo_ecommerce": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Analisi ecommerce Shopify con segnali trust e strutturati.",
        "description": "Analizza product/collection SEO, trust, conversion intent, contenuti ecommerce e segnali strutturati.",
    },
    "claude_seo_flow": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Workflow SEO end-to-end con output orchestrato.",
        "description": "Orchestrazione workflow SEO tra audit, contenuto, tecnico e reporting.",
    },
    "claude_seo_google": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Integrazione Google Search Console pianificata.",
        "description": "Report performance e indicizzazione da Google Search Console e Analytics.",
    },
    "claude_seo_firecrawl": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Crawl profondo via Firecrawl non ancora disponibile.",
        "description": "Crawl sito su larga scala via Firecrawl per audit e estrazione contenuti.",
    },
    "claude_seo_dataforseo": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Intelligence SERP via DataForSEO pianificata.",
        "description": "Dati SERP, metriche keyword e marketplace intelligence via DataForSEO.",
    },
    "claude_seo_backlinks": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Analisi backlink con API esterna pianificata.",
        "description": "Profilo backlink, link tossici e opportunità link building.",
    },
    "claude_seo_local": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Local SEO con dati locali non ancora integrati.",
        "description": "Audit local SEO: NAP, Google Business Profile, citazioni e contenuti geo.",
    },
    "claude_seo_maps": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Ottimizzazione Maps con API Google pianificata.",
        "description": "Ottimizzazione Google Maps e local listing con segnali recensioni e location.",
    },
    "claude_seo_drift_baseline": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Baseline SEO storica pianificata.",
        "description": "Snapshot baseline SEO per ranking, contenuto e salute tecnica nel tempo.",
    },
    "claude_seo_drift_compare": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Confronto drift SEO pianificato.",
        "description": "Confronta stato SEO attuale vs baseline per rilevare drift ranking e tecnico.",
    },
    "claude_seo_image_gen": {
        "ui_category": "seo_advanced",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Generazione immagini SEO con provider esterno pianificata.",
        "description": "Generazione AI di hero image, OG image e asset visual per SEO.",
    },
    "email_campaign_strategy": {
        "ui_category": "email_ads",
        "gcr_recommended_model": "gpt-5.4",
        "gcr_recommendation_reason": "Strategia campagna email strutturata.",
        "description": "Genera strategia campagne email.",
    },
    "email_copy_generation": {
        "ui_category": "email_ads",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Copy email breve e persuasivo: modello leggero.",
        "description": "Genera copy per email marketing.",
    },
    "ads_copy_generation": {
        "ui_category": "email_ads",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Varianti ads brevi: modello leggero.",
        "description": "Genera copy per annunci.",
    },
    "landing_copy_generation": {
        "ui_category": "email_ads",
        "gcr_recommended_model": "gpt-5.5",
        "gcr_recommendation_reason": "Landing lunghe: alta qualità narrativa.",
        "description": "Genera copy per landing page.",
    },
}


def _apply_gcr_metadata(op: AiOperationDefinition) -> AiOperationDefinition:
    meta = GCR_METADATA.get(op.operation_key, {})
    if not meta:
        return op
    updates: dict[str, str] = {}
    if "ui_category" in meta:
        updates["ui_category"] = meta["ui_category"]
    if "gcr_recommended_model" in meta:
        updates["gcr_recommended_model"] = meta["gcr_recommended_model"]
    if "gcr_recommendation_reason" in meta:
        updates["gcr_recommendation_reason"] = meta["gcr_recommendation_reason"]
    if "description" in meta:
        updates["description"] = meta["description"]
    return op.model_copy(update=updates)


def recommended_model_from_env(env_key: str) -> str | None:
    mapping = {
        "OPENAI_MODEL_CHEAP": settings.openai_model_cheap or settings.openai_model,
        "OPENAI_MODEL_STANDARD": settings.openai_model_standard or settings.openai_model,
        "OPENAI_MODEL_PREMIUM": settings.openai_model_premium or "gpt-4o",
        "OPENAI_MODEL_REASONING": settings.openai_model_reasoning,
        "OPENAI_MODEL_FALLBACK": (
            settings.openai_model_fallback
            or settings.openai_model_standard
            or settings.openai_model
        ),
        "OPENAI_MODEL": settings.openai_model,
    }
    raw = mapping.get(env_key)
    if raw and str(raw).strip():
        return str(raw).strip()
    return None


def _op(
    key: str,
    label: str,
    module: str,
    operation: str,
    profile: str,
    tier: str,
    env_key: str,
    max_tokens: int,
    temperature: float,
    *,
    entity_type: str | None = None,
    quality: QualityLevel = "medium",
    cost: CostSensitivity = "medium",
    description: str = "",
    recommended_use: str = "",
    warning_notes: str | None = None,
    status: OperationStatus = "implemented",
    enabled: bool = True,
) -> AiOperationDefinition:
    return AiOperationDefinition(
        operation_key=key,
        label=label,
        module=module,
        operation=operation,
        context_profile=profile,
        entity_type=entity_type,
        recommended_tier=tier,
        recommended_model_env_key=env_key,
        recommended_max_output_tokens=max_tokens,
        recommended_temperature=temperature,
        quality_level=quality,
        cost_sensitivity=cost,
        description=description or label,
        recommended_use=recommended_use,
        warning_notes=warning_notes,
        status=status,
        enabled=enabled,
    )


_SEO_SKILL_EXTERNAL_WARNING = "Richiede integrazione esterna non ancora disponibile."


def _seo_skill_op(
    skill_key: str,
    label: str,
    tier: str,
    *,
    max_tokens: int | None = None,
    temperature: float | None = None,
    context_profile: str = "seo_skill_audit",
    status: OperationStatus = "implemented",
    enabled: bool = True,
    recommended_use: str = "",
    warning_notes: str | None = None,
) -> AiOperationDefinition:
    env_key = "OPENAI_MODEL_PREMIUM" if tier == "premium" else "OPENAI_MODEL_STANDARD"
    resolved_max_tokens = (
        max_tokens if max_tokens is not None else (4500 if tier == "premium" else 3500)
    )
    resolved_temperature = (
        temperature if temperature is not None else (0.35 if tier == "premium" else 0.3)
    )
    tier_label = "Premium" if tier == "premium" else "Standard"
    return _op(
        f"claude_{skill_key}",
        label,
        "seo_skills",
        skill_key,
        context_profile,
        tier,
        env_key,
        resolved_max_tokens,
        resolved_temperature,
        recommended_use=recommended_use or f"{tier_label}: skill SEO con output JSON strutturato.",
        warning_notes=warning_notes,
        status=status,
        enabled=enabled,
    )


def _build_registry() -> dict[str, AiOperationDefinition]:
    ops: list[AiOperationDefinition] = [
        # Brand Intelligence
        _op(
            "brand_profile_enrichment",
            "Arricchimento profilo brand",
            "brand_intelligence",
            "enrich_profile",
            "minimal",
            "cheap",
            "OPENAI_MODEL_CHEAP",
            500,
            0.3,
            quality="medium",
            cost="high",
            recommended_use="Usa un modello economico: task breve con output strutturato.",
        ),
        _op(
            "brand_identity_import",
            "Import identità brand",
            "brand_intelligence",
            "import_identity",
            "brand_import",
            "standard",
            "OPENAI_MODEL_STANDARD",
            4500,
            0.4,
            recommended_use="Standard: estrazione strutturata da documenti brand.",
        ),
        _op(
            "visual_identity_extraction",
            "Estrazione identità visiva",
            "brand_intelligence",
            "extract_visual_identity",
            "brand_import",
            "standard",
            "OPENAI_MODEL_STANDARD",
            3000,
            0.35,
            status="planned",
            enabled=False,
            recommended_use="Standard: analisi palette e stile visivo.",
        ),
        _op(
            "safe_claims_import",
            "Import Safe Claims",
            "brand_intelligence",
            "import_safe_claims",
            "brand_import",
            "standard",
            "OPENAI_MODEL_STANDARD",
            4500,
            0.4,
            quality="critical",
            recommended_use="Standard: claim sanitari richiedono accuratezza.",
            warning_notes="Non usare tier cheap per validazione claim.",
        ),
        _op(
            "product_knowledge_general_import",
            "Import Product Knowledge generale",
            "brand_intelligence",
            "import_product_knowledge_general",
            "brand_import",
            "standard",
            "OPENAI_MODEL_STANDARD",
            4500,
            0.4,
            recommended_use="Standard: sintesi knowledge generale prodotto.",
        ),
        _op(
            "product_knowledge_item_import",
            "Import Product Knowledge item",
            "brand_intelligence",
            "import_product_knowledge_items",
            "brand_import",
            "standard",
            "OPENAI_MODEL_STANDARD",
            4500,
            0.4,
            recommended_use="Standard: estrazione per singolo prodotto.",
        ),
        _op(
            "faq_objections_import",
            "Import FAQ & Obiezioni",
            "brand_intelligence",
            "import_faq_objections",
            "brand_import",
            "standard",
            "OPENAI_MODEL_STANDARD",
            4500,
            0.4,
            recommended_use="Standard: parsing FAQ da file strutturati.",
        ),
        _op(
            "brand_document_extraction",
            "Estrazione documento brand",
            "brand_intelligence",
            "extract_document",
            "brand_import",
            "standard",
            "OPENAI_MODEL_STANDARD",
            4500,
            0.4,
            recommended_use="Standard: estrazione fatti da PDF/documenti.",
        ),
        _op(
            "brand_synthesis",
            "Sintesi sezione brand",
            "brand_intelligence",
            "synthesize_section",
            "brand_import",
            "standard",
            "OPENAI_MODEL_STANDARD",
            4500,
            0.4,
            recommended_use="Standard: sintesi moduli BI da fatti estratti.",
        ),
        _op(
            "brand_brief_synthesis",
            "Sintesi brief brand",
            "brand_intelligence",
            "generate_brief_from_batch",
            "brand_import",
            "standard",
            "OPENAI_MODEL_STANDARD",
            4500,
            0.4,
            recommended_use="Standard: brief intelligence da batch import.",
        ),
        # Product & Collection SEO
        _op(
            "product_seo_field",
            "Campo SEO prodotto",
            "product_seo",
            "generate_field",
            "product_seo_field",
            "cheap",
            "OPENAI_MODEL_CHEAP",
            400,
            0.35,
            entity_type="product",
            cost="high",
            recommended_use="Usa cheap: singolo campo, output breve e schema rigido.",
        ),
        _op(
            "collection_seo_field",
            "Campo SEO collection",
            "content_seo",
            "generate_field",
            "collection_seo_field",
            "cheap",
            "OPENAI_MODEL_CHEAP",
            400,
            0.35,
            entity_type="collection",
            cost="high",
            recommended_use="Usa cheap: meta title/description collection.",
        ),
        _op(
            "product_image_alt",
            "Alt immagine prodotto",
            "product_seo",
            "generate_field",
            "image_alt",
            "cheap",
            "OPENAI_MODEL_CHEAP",
            120,
            0.3,
            entity_type="product_image",
            cost="high",
            quality="low",
            recommended_use="Usa un modello economico: il task è breve e controllato da schema.",
        ),
        _op(
            "collection_image_alt",
            "Alt immagine collection",
            "content_seo",
            "generate_field",
            "image_alt",
            "cheap",
            "OPENAI_MODEL_CHEAP",
            120,
            0.3,
            entity_type="collection",
            cost="high",
            status="planned",
            enabled=False,
            recommended_use="Usa cheap: alt testuale breve.",
        ),
        _op(
            "product_seo_full_proposal",
            "Proposta SEO prodotto completa",
            "product_seo",
            "generate_proposal",
            "product_seo_full",
            "standard",
            "OPENAI_MODEL_STANDARD",
            2500,
            0.45,
            recommended_use="Standard: proposta multi-campo con contesto brand.",
        ),
        _op(
            "collection_seo_full_proposal",
            "Proposta SEO collection completa",
            "content_seo",
            "generate_proposal",
            "collection_seo_full",
            "standard",
            "OPENAI_MODEL_STANDARD",
            2500,
            0.45,
            recommended_use="Standard: proposta SEO collection completa.",
        ),
        _op(
            "seo_compliance_review",
            "Revisione compliance SEO",
            "content_seo",
            "compliance_review",
            "compliance_review",
            "standard",
            "OPENAI_MODEL_REASONING",
            1500,
            0.2,
            quality="critical",
            recommended_use="Reasoning o standard forte: validazione claim e tono.",
            warning_notes="Mai tier cheap per compliance.",
            status="planned",
            enabled=False,
        ),
        # Blog & Ricette
        _op(
            "editorial_plan_generation",
            "Piano editoriale",
            "content_seo",
            "generate_editorial_plan",
            "generic",
            "standard",
            "OPENAI_MODEL_STANDARD",
            2000,
            0.45,
            status="non_ai",
            enabled=False,
            recommended_use="Rule-based: non usa AI.",
        ),
        _op(
            "blog_brief_generation",
            "Generazione brief blog",
            "blog_brief",
            "generate_brief",
            "blog_brief",
            "standard",
            "OPENAI_MODEL_STANDARD",
            3000,
            0.5,
            quality="high",
            recommended_use="Standard: brief strutturato con brand context.",
        ),
        _op(
            "blog_brief_batch_item",
            "Brief blog (batch)",
            "blog_brief",
            "batch_brief_item",
            "blog_brief",
            "standard",
            "OPENAI_MODEL_STANDARD",
            3000,
            0.5,
            quality="high",
            recommended_use="Standard: stesso tier del brief singolo.",
        ),
        _op(
            "article_draft_generation",
            "Generazione articolo",
            "article_generator",
            "generate_article",
            "article_draft",
            "premium",
            "OPENAI_MODEL_PREMIUM",
            8000,
            0.55,
            quality="critical",
            cost="low",
            recommended_use="Usa premium: richiede tono, struttura, claim e qualità narrativa.",
            warning_notes="Non usare cheap: qualità articolo degrada.",
        ),
        _op(
            "editorial_image_generation",
            "Immagine hero editoriale",
            "content_seo",
            "generate_editorial_image",
            "editorial_image",
            "standard",
            "OPENAI_MODEL_STANDARD",
            800,
            0.4,
            entity_type="editorial_item",
            recommended_use="Genera prompt e immagine hero da articolo e brand context.",
        ),
        _op(
            "editorial_image_edit",
            "Modifica immagine editoriale",
            "content_seo",
            "edit_editorial_image",
            "editorial_image",
            "standard",
            "OPENAI_MODEL_STANDARD",
            800,
            0.4,
            entity_type="editorial_item",
            recommended_use="Rigenera immagine hero con istruzioni di modifica.",
        ),
        _op(
            "article_rewrite",
            "Riscrittura articolo",
            "article_generator",
            "rewrite_article",
            "article_draft",
            "premium",
            "OPENAI_MODEL_PREMIUM",
            6000,
            0.55,
            status="planned",
            enabled=False,
            recommended_use="Premium: riscrittura mantiene tono brand.",
        ),
        _op(
            "article_meta_generation",
            "Meta articolo",
            "article_generator",
            "generate_meta",
            "product_seo_field",
            "cheap",
            "OPENAI_MODEL_CHEAP",
            400,
            0.35,
            status="planned",
            enabled=False,
            recommended_use="Cheap: meta title/description brevi.",
        ),
        _op(
            "article_compliance_review",
            "Compliance articolo",
            "article_generator",
            "compliance_review",
            "compliance_review",
            "standard",
            "OPENAI_MODEL_REASONING",
            1500,
            0.2,
            quality="critical",
            status="planned",
            enabled=False,
            recommended_use="Reasoning: revisione claim su articolo lungo.",
        ),
        # PED/Social futuri
        _op("ped_strategy", "Strategia PED", "ped", "generate_strategy", "generic", "premium", "OPENAI_MODEL_PREMIUM", 4000, 0.5, status="planned", enabled=False, recommended_use="Premium per strategia avanzata."),
        _op("ped_calendar_generation", "Calendario PED", "ped", "generate_calendar", "generic", "standard", "OPENAI_MODEL_STANDARD", 3000, 0.45, status="planned", enabled=False, recommended_use="Standard per calendario editoriale."),
        _op("ped_post_copy", "Copy post PED", "ped", "generate_post_copy", "social_response", "cheap", "OPENAI_MODEL_CHEAP", 1200, 0.7, status="planned", enabled=False, recommended_use="Cheap per copy breve social."),
        _op("ped_creative_prompt", "Prompt creativo PED", "ped", "generate_creative_prompt", "generic", "standard", "OPENAI_MODEL_STANDARD", 1500, 0.6, status="planned", enabled=False, recommended_use="Standard per prompt creativi."),
        _op("ped_image_prompt", "Prompt immagine PED", "ped", "generate_image_prompt", "minimal", "cheap", "OPENAI_MODEL_CHEAP", 800, 0.5, status="planned", enabled=False, recommended_use="Cheap per prompt immagine breve."),
        _op("social_comment_response", "Risposta commento social", "social", "generate_response", "social_response", "cheap", "OPENAI_MODEL_CHEAP", 600, 0.4, status="planned", enabled=False, recommended_use="Cheap per risposte brevi."),
        # SEO futuri
        _op("seo_keyword_research", "Keyword research", "content_seo", "keyword_research", "generic", "standard", "OPENAI_MODEL_STANDARD", 2500, 0.45, status="planned", enabled=False, recommended_use="Standard per ricerca keyword."),
        _op("seo_content_gap_analysis", "Content gap analysis", "content_seo", "content_gap", "generic", "standard", "OPENAI_MODEL_STANDARD", 2500, 0.4, status="planned", enabled=False, recommended_use="Standard per gap analysis."),
        _op("seo_article_outline", "Outline articolo SEO", "content_seo", "article_outline", "blog_brief", "standard", "OPENAI_MODEL_STANDARD", 2500, 0.5, status="planned", enabled=False, recommended_use="Standard per outline."),
        _op("seo_article_generation", "Articolo SEO", "content_seo", "generate_seo_article", "article_draft", "premium", "OPENAI_MODEL_PREMIUM", 6000, 0.6, status="planned", enabled=False, recommended_use="Premium per articoli SEO lunghi."),
        _op("seo_article_optimization", "Ottimizzazione articolo SEO", "content_seo", "optimize_article", "article_draft", "standard", "OPENAI_MODEL_STANDARD", 3000, 0.45, status="planned", enabled=False, recommended_use="Standard per ottimizzazione."),
        # Claude SEO Skill Library
        _seo_skill_op("seo_audit", "SEO Audit sito", "premium"),
        _seo_skill_op(
            "seo_page",
            "SEO pagina singola",
            "standard",
            max_tokens=6000,
            temperature=0.30,
        ),
        _seo_skill_op("seo_technical", "SEO tecnico", "premium"),
        _seo_skill_op(
            "seo_content",
            "SEO contenuto",
            "premium",
            max_tokens=6500,
            temperature=0.30,
        ),
        _seo_skill_op(
            "seo_content_brief",
            "Brief contenuto SEO",
            "standard",
            max_tokens=6000,
            temperature=0.30,
        ),
        _seo_skill_op(
            "seo_schema",
            "Schema markup SEO",
            "standard",
            max_tokens=5000,
            temperature=0.20,
        ),
        _seo_skill_op(
            "seo_geo",
            "AI Search / GEO audit",
            "premium",
            max_tokens=6500,
            temperature=0.30,
        ),
        _seo_skill_op(
            "seo_images",
            "SEO immagini",
            "standard",
            max_tokens=4500,
            temperature=0.25,
        ),
        _seo_skill_op("seo_sitemap_analyze", "Analisi sitemap", "standard"),
        _seo_skill_op("seo_sitemap_generate", "Generazione sitemap", "standard"),
        _seo_skill_op(
            "seo_plan",
            "Piano SEO strategico",
            "premium",
            max_tokens=4500,
            temperature=0.30,
        ),
        _seo_skill_op(
            "seo_competitor_pages",
            "Pagine competitor",
            "premium",
            max_tokens=4500,
            temperature=0.30,
        ),
        _seo_skill_op(
            "seo_hreflang",
            "Hreflang audit",
            "standard",
            max_tokens=3500,
            temperature=0.30,
        ),
        _seo_skill_op(
            "seo_programmatic",
            "Programmatic SEO",
            "premium",
            max_tokens=4500,
            temperature=0.30,
        ),
        _seo_skill_op(
            "seo_cluster",
            "Keyword clustering",
            "premium",
            max_tokens=4500,
            temperature=0.30,
        ),
        _seo_skill_op(
            "seo_sxo",
            "Search Experience Optimization",
            "premium",
            max_tokens=6500,
            temperature=0.30,
        ),
        _seo_skill_op(
            "seo_ecommerce",
            "SEO ecommerce",
            "premium",
            max_tokens=6500,
            temperature=0.30,
        ),
        _seo_skill_op("seo_flow", "Workflow SEO", "premium"),
        _seo_skill_op(
            "seo_google",
            "Google Search Console",
            "premium",
            status="planned",
            enabled=False,
            warning_notes=_SEO_SKILL_EXTERNAL_WARNING,
        ),
        _seo_skill_op(
            "seo_firecrawl",
            "Crawl Firecrawl",
            "premium",
            status="planned",
            enabled=False,
            warning_notes=_SEO_SKILL_EXTERNAL_WARNING,
        ),
        _seo_skill_op(
            "seo_dataforseo",
            "Intelligence DataForSEO",
            "premium",
            status="planned",
            enabled=False,
            warning_notes=_SEO_SKILL_EXTERNAL_WARNING,
        ),
        _seo_skill_op(
            "seo_backlinks",
            "Analisi backlink",
            "premium",
            status="planned",
            enabled=False,
            warning_notes=_SEO_SKILL_EXTERNAL_WARNING,
        ),
        _seo_skill_op(
            "seo_local",
            "Local SEO",
            "premium",
            status="planned",
            enabled=False,
            warning_notes=_SEO_SKILL_EXTERNAL_WARNING,
        ),
        _seo_skill_op(
            "seo_maps",
            "Google Maps / local listings",
            "premium",
            status="planned",
            enabled=False,
            warning_notes=_SEO_SKILL_EXTERNAL_WARNING,
        ),
        _seo_skill_op(
            "seo_drift_baseline",
            "SEO drift baseline",
            "premium",
            status="planned",
            enabled=False,
            warning_notes=_SEO_SKILL_EXTERNAL_WARNING,
        ),
        _seo_skill_op(
            "seo_drift_compare",
            "SEO drift compare",
            "premium",
            status="planned",
            enabled=False,
            warning_notes=_SEO_SKILL_EXTERNAL_WARNING,
        ),
        _seo_skill_op(
            "seo_image_gen",
            "Generazione immagini SEO",
            "premium",
            status="planned",
            enabled=False,
            warning_notes=_SEO_SKILL_EXTERNAL_WARNING,
        ),
        # Growth Audit
        _op(
            "growth_audit_page_ai_analysis",
            "Analisi AI/GEO/CRO pagina Growth Audit",
            "growth_audit",
            "page_ai_analysis",
            "growth_audit_page_ai",
            "standard",
            "OPENAI_MODEL_STANDARD",
            6500,
            0.25,
            entity_type="growth_audit_page",
            recommended_use="Analisi singola pagina prioritaria: SEO/GEO/CRO/Ads readiness.",
        ),
        # Email/Ads futuri
        _op("email_campaign_strategy", "Strategia email", "email", "campaign_strategy", "generic", "premium", "OPENAI_MODEL_PREMIUM", 4000, 0.5, status="planned", enabled=False, recommended_use="Premium per strategia campagna complessa."),
        _op("email_copy_generation", "Copy email", "email", "generate_copy", "generic", "standard", "OPENAI_MODEL_STANDARD", 2500, 0.55, status="planned", enabled=False, recommended_use="Standard per email marketing."),
        _op("ads_copy_generation", "Copy ads", "ads", "generate_copy", "generic", "standard", "OPENAI_MODEL_STANDARD", 1500, 0.6, status="planned", enabled=False, recommended_use="Standard per varianti ads."),
        _op("landing_copy_generation", "Copy landing", "ads", "generate_landing", "article_draft", "premium", "OPENAI_MODEL_PREMIUM", 5000, 0.55, status="planned", enabled=False, recommended_use="Premium per landing lunghe."),
    ]
    enriched = [_apply_gcr_metadata(op) for op in ops]
    return {op.operation_key: op for op in enriched}


AI_OPERATIONS: dict[str, AiOperationDefinition] = _build_registry()

_INFERENCE_INDEX: list[tuple[str, str, str, str | None, str]] = [
    (op.module, op.operation, op.context_profile, op.entity_type, op.operation_key)
    for op in AI_OPERATIONS.values()
    if op.status == "implemented"
]


def get_operation(operation_key: str) -> AiOperationDefinition | None:
    return AI_OPERATIONS.get(operation_key)


def get_operation_key_for_seo_skill(skill_key: str) -> str:
    normalized = skill_key.strip()
    if not normalized:
        raise ValueError("skill_key vuoto")
    operation_key = normalized if normalized.startswith("claude_") else f"claude_{normalized}"
    if operation_key not in AI_OPERATIONS:
        raise ValueError(f"Operazione SEO Skill non registrata: {skill_key}")
    return operation_key


def list_operations(*, include_planned: bool = True) -> list[AiOperationDefinition]:
    ops = list(AI_OPERATIONS.values())
    if not include_planned:
        ops = [o for o in ops if o.status == "implemented"]
    return sorted(ops, key=lambda o: (o.status != "implemented", o.label))


def infer_operation_key(
    module: str,
    operation: str,
    context_profile: str | None,
    entity_type: str | None = None,
) -> str | None:
    profile = context_profile or "generic"
    best: str | None = None
    best_score = -1
    for mod, op, prof, etype, key in _INFERENCE_INDEX:
        score = 0
        if mod != module:
            continue
        score += 2
        if op != operation:
            continue
        score += 4
        if prof != profile:
            continue
        score += 2
        if etype is not None and entity_type is not None:
            if etype != entity_type:
                continue
            score += 2
        elif etype is None and entity_type is not None:
            score += 0
        if score > best_score:
            best_score = score
            best = key
    return best


def resolve_registry_model(op: AiOperationDefinition) -> str | None:
    return recommended_model_from_env(op.recommended_model_env_key)
