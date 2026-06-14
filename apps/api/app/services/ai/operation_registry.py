"""Central registry of AI operations in Growth Control Room."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel

from app.core.config import settings

QualityLevel = Literal["low", "medium", "high", "critical"]
CostSensitivity = Literal["low", "medium", "high"]
OperationStatus = Literal["implemented", "planned", "non_ai"]


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

    model_config = {"populate_by_name": True}


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
        # Email/Ads futuri
        _op("email_campaign_strategy", "Strategia email", "email", "campaign_strategy", "generic", "premium", "OPENAI_MODEL_PREMIUM", 4000, 0.5, status="planned", enabled=False, recommended_use="Premium per strategia campagna complessa."),
        _op("email_copy_generation", "Copy email", "email", "generate_copy", "generic", "standard", "OPENAI_MODEL_STANDARD", 2500, 0.55, status="planned", enabled=False, recommended_use="Standard per email marketing."),
        _op("ads_copy_generation", "Copy ads", "ads", "generate_copy", "generic", "standard", "OPENAI_MODEL_STANDARD", 1500, 0.6, status="planned", enabled=False, recommended_use="Standard per varianti ads."),
        _op("landing_copy_generation", "Copy landing", "ads", "generate_landing", "article_draft", "premium", "OPENAI_MODEL_PREMIUM", 5000, 0.55, status="planned", enabled=False, recommended_use="Premium per landing lunghe."),
    ]
    return {op.operation_key: op for op in ops}


AI_OPERATIONS: dict[str, AiOperationDefinition] = _build_registry()

_INFERENCE_INDEX: list[tuple[str, str, str, str | None, str]] = [
    (op.module, op.operation, op.context_profile, op.entity_type, op.operation_key)
    for op in AI_OPERATIONS.values()
    if op.status == "implemented"
]


def get_operation(operation_key: str) -> AiOperationDefinition | None:
    return AI_OPERATIONS.get(operation_key)


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
