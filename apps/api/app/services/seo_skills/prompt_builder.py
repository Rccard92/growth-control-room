"""Build structured system and user prompts for Claude SEO Skill Library."""

from __future__ import annotations

import json
import re
from typing import Any

from app.schemas.seo_skills import SeoSkillCatalogItem
from app.services.seo_skills.output_schema import get_output_schema_instruction

MAX_PROMPT_HTML_CHARS = 60_000
MAX_PROMPT_TEXT_CHARS = 30_000
MAX_PROMPT_BRAND_CONTEXT_CHARS = 10_000
MAX_PROMPT_METADATA_CHARS = 15_000
MAX_PROMPT_SHOPIFY_CHARS = 20_000

_SENSITIVE_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "token",
    "password",
    "secret",
    "authorization",
    "bearer",
)
_SENSITIVE_STRING_PATTERNS = (
    re.compile(r"(?i)\bbearer\s+[a-z0-9._\-]+"),
    re.compile(r"(?i)\bapi[_-]?key\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bauthorization\s*[:=]\s*\S+"),
    re.compile(r"(?i)\btoken\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bpassword\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bsecret\s*[:=]\s*\S+"),
)

SKILL_SPECIFIC_INSTRUCTIONS: dict[str, str] = {
    "seo_schema": (
        "Concentrati su Schema.org e JSON-LD: Product, BreadcrumbList, Organization, "
        "WebSite e FAQPage solo se utile e realmente supportata dal contenuto. "
        "Verifica coerenza tra dati visibili in pagina e markup strutturato. "
        "Evidenzia errori comuni ecommerce e suggerisci snippet JSON-LD in artifacts.jsonLd."
    ),
    "seo_geo": (
        "Concentrati su AI Search / GEO: citability, entità nominate, chiarezza semantica, "
        "blocchi risposta, autorevolezza, frasi citabili e completezza informativa. "
        "Valuta se la pagina può essere usata come fonte da AI overview o search assistant."
    ),
    "seo_ecommerce": (
        "Concentrati su product SEO e collection SEO: intento commerciale, trust, "
        "informazioni prodotto, prezzo/disponibilità se presenti, shipping/returns se presenti, "
        "obiezioni d'acquisto, contenuti utili alla conversione e structured data ecommerce."
    ),
    "seo_images": (
        "Concentrati su alt text, naming file, peso immagini, formati moderni, lazy loading, "
        "srcset, dimensioni, CLS potenziale, coerenza immagini/prodotto e opportunità Google Images."
    ),
    "seo_page": (
        "Concentrati su title, meta description, H1/H2, canonical, Open Graph, contenuto principale, "
        "internal linking, schema, immagini, search intent e ottimizzazione snippet SERP."
    ),
    "seo_content": (
        "Concentrati su qualità contenuto, E-E-A-T, utilità, profondità, freschezza, intent match, "
        "sezioni mancanti, domande utente, chiarezza e trust."
    ),
    "seo_content_brief": (
        "Concentrati su brief editoriale: struttura H1/H2/H3, search intent, domande da coprire, "
        "entità, keyword cluster, sezioni consigliate, angle commerciale/editoriale e internal link suggeriti."
    ),
    "seo_sxo": (
        "Concentrati su search experience optimization: esperienza post-click, leggibilità, "
        "struttura visiva, chiarezza CTA, riduzione attrito, intent match, fiducia e percorso utente."
    ),
    "seo_cluster": (
        "Concentrati su cluster semantici: pillar page, supporting content, collegamenti interni, "
        "topical authority, cannibalizzazione potenziale e gap contenuto."
    ),
    "seo_plan": (
        "Concentrati su roadmap SEO operativa: priorità, quick wins, interventi tecnici, contenuti, "
        "schema, ecommerce e monitoraggio."
    ),
    "seo_competitor_pages": (
        "Concentrati su confronto pagina vs standard competitor: gap contenuto, trust, UX e schema. "
        "Non inventare competitor se non forniti; se assenti, usa benchmark generico e segnala warning."
    ),
    "seo_programmatic": (
        "Concentrati su template SEO scalabili: pattern contenuto, variabili pagina, regole title/meta, "
        "sezioni dinamiche, rischi thin content e differenziazione pagine."
    ),
    "seo_hreflang": (
        "Concentrati su internazionalizzazione: hreflang, canonical cross-language e coerenza URL. "
        "Indica limiti se non ci sono lingue multiple nei dati disponibili."
    ),
}


def _safe_truncate(value: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(value) <= max_chars:
        return value
    if max_chars <= 3:
        return value[:max_chars]
    return value[: max_chars - 3] + "..."


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower().replace("-", "_")
    return any(fragment in lowered for fragment in _SENSITIVE_KEY_FRAGMENTS)


def _mask_sensitive_string(value: str) -> str:
    masked = value
    for pattern in _SENSITIVE_STRING_PATTERNS:
        masked = pattern.sub("[REDACTED]", masked)
    return masked


def mask_sensitive_values(value: Any) -> Any:
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for key, item in value.items():
            if _is_sensitive_key(str(key)):
                masked[key] = "[REDACTED]"
            else:
                masked[key] = mask_sensitive_values(item)
        return masked
    if isinstance(value, list):
        return [mask_sensitive_values(item) for item in value]
    if isinstance(value, str):
        return _mask_sensitive_string(value)
    return value


def _generic_skill_instructions(skill_item: SeoSkillCatalogItem) -> str:
    return (
        f"Applica un'analisi SEO coerente con la skill '{skill_item.label}': "
        f"{skill_item.description}"
    )


def _get_skill_specific_instructions(
    skill_item: SeoSkillCatalogItem,
) -> str:
    return SKILL_SPECIFIC_INSTRUCTIONS.get(
        skill_item.key,
        _generic_skill_instructions(skill_item),
    )


def _build_target_summary(skill_input: dict[str, Any]) -> str:
    target_type = skill_input.get("targetType") or "—"
    target_id = skill_input.get("targetId") or "—"
    url = skill_input.get("url") or "—"
    title = skill_input.get("title") or "—"
    return (
        f"Target type: {target_type}\n"
        f"Target id: {target_id}\n"
        f"URL: {url}\n"
        f"Title: {title}"
    )


def _format_json_block(label: str, value: Any, max_chars: int) -> str:
    if value in (None, "", {}, []):
        return ""
    serialized = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    serialized = _safe_truncate(serialized, max_chars)
    return f"{label}:\n{serialized}"


def _format_brand_context(skill_input: dict[str, Any]) -> str:
    brand_context = skill_input.get("brandContext")
    if not brand_context:
        return ""
    text = _safe_truncate(str(brand_context), MAX_PROMPT_BRAND_CONTEXT_CHARS)
    return f"Brand context:\n{text}"


def _format_shopify_context(skill_input: dict[str, Any]) -> str:
    shopify = skill_input.get("shopify")
    return _format_json_block("Shopify context", shopify, MAX_PROMPT_SHOPIFY_CHARS)


def _format_metadata_context(skill_input: dict[str, Any]) -> str:
    metadata = skill_input.get("metadata")
    return _format_json_block("Metadata", metadata, MAX_PROMPT_METADATA_CHARS)


def _format_warnings(skill_input: dict[str, Any]) -> str:
    warnings = skill_input.get("warnings")
    if not isinstance(warnings, list) or not warnings:
        return ""
    lines = "\n".join(f"- {warning}" for warning in warnings if warning)
    return f"Input warnings:\n{lines}"


def build_skill_system_prompt(
    skill_item: SeoSkillCatalogItem,
    skill_input: dict[str, Any],
) -> str:
    del skill_input  # Brand context is referenced in user prompt; system explains usage rules.
    skill_specific = _get_skill_specific_instructions(skill_item)
    schema_instruction = get_output_schema_instruction(skill_item.key)

    sections = [
        (
            "Sei un SEO specialist senior che opera dentro Growth Control Room (GCR). "
            "La skill è ispirata a Claude SEO ed è adattata al contesto operativo GCR."
        ),
        (
            f"Skill key: {skill_item.key}\n"
            f"Skill label: {skill_item.label}\n"
            f"Descrizione: {skill_item.description}\n"
            f"Comando upstream: {skill_item.upstream_command}"
        ),
        f"Istruzioni specifiche skill:\n{skill_specific}",
        (
            "Regole di output:\n"
            "- Rispondi con SOLO JSON valido.\n"
            "- Non usare markdown fuori dal JSON.\n"
            "- Non aggiungere testo prima o dopo il JSON.\n"
            "- Non inventare claim, metriche o dati non supportati dall'input.\n"
            "- Basa findings su evidenze tratte dall'input quando possibile.\n"
            "- Fornisci raccomandazioni operative e task eseguibili.\n"
            "- Se un dato manca, inseriscilo in warnings e non inventarlo.\n"
            "- Usa Brand Intelligence dal contesto utente quando presente."
        ),
        f"Schema output obbligatorio:\n{schema_instruction}",
    ]
    return "\n\n".join(section for section in sections if section)


def build_skill_user_prompt(
    skill_item: SeoSkillCatalogItem,
    skill_input: dict[str, Any],
) -> str:
    del skill_item
    sanitized = mask_sensitive_values(skill_input)

    html = _safe_truncate(str(sanitized.get("html") or ""), MAX_PROMPT_HTML_CHARS)
    text = _safe_truncate(str(sanitized.get("text") or ""), MAX_PROMPT_TEXT_CHARS)

    sections = [
        "Analizza il target seguente e produci un output concreto, non generico.",
        _build_target_summary(sanitized),
    ]
    if html:
        sections.append(f"HTML (troncato se necessario):\n{html}")
    if text:
        sections.append(f"Testo estratto (troncato se necessario):\n{text}")

    metadata_block = _format_metadata_context(sanitized)
    if metadata_block:
        sections.append(metadata_block)

    shopify_block = _format_shopify_context(sanitized)
    if shopify_block:
        sections.append(shopify_block)

    brand_block = _format_brand_context(sanitized)
    if brand_block:
        sections.append(brand_block)

    warnings_block = _format_warnings(sanitized)
    if warnings_block:
        sections.append(warnings_block)

    sections.append(
        "Richiedi analisi concreta con severity e priority coerenti con l'impatto reale. "
        "Usa la stessa lingua del contenuto analizzato quando deducibile; altrimenti usa italiano."
    )
    return "\n\n".join(section for section in sections if section)
