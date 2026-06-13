"""Single-field SEO proposal generation (stateless — no DB draft)."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_seo import ShopifyCollection
from app.models.seo_optimizer import SeoEntityAnalysis
from app.models.shopify import ShopifyProduct, ShopifyProductMetafield, ShopifyStore
from app.services.ai.openai_client import (
    OpenAINotConfiguredError,
    OpenAIRequestError,
    generate_structured_json,
    is_openai_configured,
)
from app.services.content.seo_proposal_engine import (
    _ai_system_prompt,
    _proposed_alt_for_product,
    _rules_collection_proposal,
    _rules_product_proposal,
    _truncate_alt,
    collection_current_values,
    product_current_values,
)
from app.services.content.seo_skill_loader import load_seo_skill_context
from app.services.shopify.metafield_utils import (
    is_ai_generatable_metafield_type,
    rules_metafield_fallback,
)

FIELD_MAP: dict[str, tuple[str | None, str | None]] = {
    "title": ("product_title", "collection_title"),
    "handle": ("handle", "handle"),
    "seoTitle": ("seo_title", "seo_title"),
    "metaDescription": ("meta_description", "meta_description"),
    "descriptionHtml": ("description_html", "description_html"),
    "imageAlt": ("image_alts", "image_alt"),
    "metafield": (None, None),
}

FIELD_PROMPTS: dict[str, str] = {
    "title": "Genera solo un titolo prodotto/collection chiaro e descrittivo. Non cambiare altri campi.",
    "handle": "Genera solo un handle URL SEO-friendly (lowercase, trattini). Non cambiare il titolo.",
    "seoTitle": "Genera solo un SEO title (max 60 caratteri). Non cambiare altri campi.",
    "metaDescription": (
        "Genera solo una meta description SEO persuasiva e realistica (max 160 caratteri). "
        "Non cambiare altri campi."
    ),
    "descriptionHtml": (
        "Genera solo una descrizione HTML per ecommerce (paragrafi semplici). Non cambiare altri campi."
    ),
    "imageAlt": "Genera solo alt text descrittivo per l'immagine (10-125 caratteri). Non cambiare altri campi.",
    "metafield": "Genera SOLO il valore di questo metafield. Non cambiare altri campi.",
}


def _resolve_snake_field(entity_type: str, field: str) -> str:
    if field == "metafield":
        return "metafield"
    mapping = FIELD_MAP.get(field)
    if not mapping:
        raise ValueError(f"Campo non supportato: {field}")
    snake = mapping[0] if entity_type == "product" else mapping[1]
    if snake is None:
        raise ValueError(f"Campo {field} non supportato per {entity_type}")
    return snake


def _rules_single_field(
    entity_type: str,
    field: str,
    entity: ShopifyProduct | ShopifyCollection,
    analysis: SeoEntityAnalysis,
    current: dict[str, Any],
    image_id: str | None,
) -> tuple[Any, str, str]:
    full = (
        _rules_product_proposal(entity, analysis)
        if entity_type == "product"
        else _rules_collection_proposal(entity, analysis)
    )
    snake = _resolve_snake_field(entity_type, field)
    risk = str(full.get("risk_level", "low"))

    if field == "imageAlt" and entity_type == "product":
        if not image_id:
            raise ValueError("image_id richiesto per imageAlt prodotto")
        media = current.get("media_images") or []
        target = next(
            (m for m in media if str(m.get("id") or "") == str(image_id)),
            None,
        )
        if target is None:
            raise ValueError("Immagine non trovata")
        if isinstance(entity, ShopifyProduct):
            proposed_alt = _proposed_alt_for_product(entity, target)
        else:
            proposed_alt = _truncate_alt(str(entity.title or "Collection"))
        value = {
            "image_id": image_id,
            "current_alt": target.get("altText") or target.get("alt") or "",
            "proposed_alt": proposed_alt,
            "reason": "Alt text descrittivo derivato da titolo e contesto",
        }
        return value, value["reason"], risk

    value = full.get(snake)
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"Nessun valore generabile per {field}")
    reasoning = f"Proposta rule-based per {field}"
    return value, reasoning, risk


async def _load_metafield_row(
    store: ShopifyStore,
    session: AsyncSession,
    product_id: UUID,
    metafield_id: str,
) -> ShopifyProductMetafield:
    try:
        mf_uuid = UUID(metafield_id)
    except ValueError as exc:
        raise ValueError("metafield_id non valido") from exc
    row = (
        await session.execute(
            select(ShopifyProductMetafield).where(
                ShopifyProductMetafield.id == mf_uuid,
                ShopifyProductMetafield.shopify_store_id == store.id,
                ShopifyProductMetafield.product_id == product_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise ValueError("Metafield non trovato")
    return row


def _rules_metafield(
    metafield: ShopifyProductMetafield,
    entity: ShopifyProduct,
) -> tuple[str, str, str]:
    return rules_metafield_fallback(
        value=metafield.value,
        namespace=metafield.namespace,
        key=metafield.key,
        type_name=metafield.type,
        definition_name=metafield.definition_name,
        product_title=entity.title,
    )


def _ai_field_user_prompt(
    *,
    entity_type: str,
    field: str,
    snake_field: str,
    current: dict[str, Any],
    analysis: SeoEntityAnalysis,
    image_id: str | None,
    metafield: ShopifyProductMetafield | None = None,
) -> str:
    extra = ""
    if field == "imageAlt" and entity_type == "product":
        extra = (
            f'\nimage_id target="{image_id}". '
            'Rispondi con value come oggetto: '
            '{"image_id":"...","proposed_alt":"...","reason":"..."}'
        )
    if field == "metafield" and metafield is not None:
        extra = (
            f"\nmetafield namespace={metafield.namespace} key={metafield.key} "
            f"type={metafield.type} current_value={metafield.value or ''}\n"
            f"definition_name={metafield.definition_name or ''}\n"
            f"definition_description={metafield.definition_description or ''}\n"
            "Rispondi con value come stringa (solo il valore del metafield)."
        )
    return (
        f"entity_type={entity_type}\n"
        f"field={field}\n"
        f"snake_field={snake_field}\n"
        f"current_values={current}\n"
        f"issues={analysis.issues}\n"
        f"recommendations={analysis.recommendations}\n"
        f"{FIELD_PROMPTS.get(field, 'Genera solo il campo richiesto.')}\n"
        "Rispondi SOLO con JSON: "
        '{"value": <stringa o oggetto per imageAlt>, "reasoning": "...", "risk_level": "low|medium|high"}'
        f"{extra}"
    )


async def generate_seo_proposal_field(
    store: ShopifyStore,
    session: AsyncSession,
    *,
    entity_type: str,
    entity_id: UUID,
    field: str,
    image_id: str | None = None,
    metafield_id: str | None = None,
    use_ai: bool = True,
) -> dict[str, Any]:
    if field not in FIELD_MAP:
        raise ValueError(f"Campo non supportato: {field}")
    if field == "metafield" and entity_type != "product":
        raise ValueError("I metafield sono supportati solo per i prodotti")
    if field == "metafield" and not metafield_id:
        raise ValueError("metafield_id richiesto per field=metafield")

    analysis = (
        await session.execute(
            select(SeoEntityAnalysis).where(
                SeoEntityAnalysis.project_id == store.project_id,
                SeoEntityAnalysis.shopify_store_id == store.id,
                SeoEntityAnalysis.entity_type == entity_type,
                SeoEntityAnalysis.entity_id == entity_id,
            )
        )
    ).scalar_one_or_none()
    if analysis is None:
        raise ValueError("Esegui prima l'analisi SEO su questa entità")

    metafield_row: ShopifyProductMetafield | None = None
    if entity_type == "product":
        entity = (
            await session.execute(
                select(ShopifyProduct).where(
                    ShopifyProduct.id == entity_id,
                    ShopifyProduct.shopify_store_id == store.id,
                )
            )
        ).scalar_one_or_none()
        if entity is None:
            raise ValueError("Prodotto non trovato")
        current = product_current_values(entity)
        if field == "metafield":
            metafield_row = await _load_metafield_row(store, session, entity_id, metafield_id or "")
            if not is_ai_generatable_metafield_type(metafield_row.type, metafield_row.value or ""):
                raise ValueError(
                    "Questo tipo di metafield non è ancora modificabile da Growth Control Room."
                )
    elif entity_type == "collection":
        entity = (
            await session.execute(
                select(ShopifyCollection).where(
                    ShopifyCollection.id == entity_id,
                    ShopifyCollection.shopify_store_id == store.id,
                )
            )
        ).scalar_one_or_none()
        if entity is None:
            raise ValueError("Collection non trovata")
        current = collection_current_values(entity)
    else:
        raise ValueError("entity_type non supportato")

    snake_field = _resolve_snake_field(entity_type, field)
    if field == "imageAlt" and entity_type == "product" and not image_id:
        raise ValueError("image_id richiesto per imageAlt prodotto")

    skill_ctx = load_seo_skill_context()
    value: Any
    reasoning: str
    risk_level: str

    if field == "metafield" and metafield_row is not None:
        if use_ai and is_openai_configured():
            system_prompt = _ai_system_prompt(skill_ctx.as_proposal_prompt_context())
            user_prompt = _ai_field_user_prompt(
                entity_type=entity_type,
                field=field,
                snake_field=snake_field,
                current=current,
                analysis=analysis,
                image_id=image_id,
                metafield=metafield_row,
            )
            try:
                result = await generate_structured_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
                value = result.get("value")
                reasoning = str(result.get("reasoning") or "")
                risk_level = str(result.get("risk_level") or "low")
                if value is None or (isinstance(value, str) and not str(value).strip()):
                    raise OpenAIRequestError("Risposta AI senza valore utilizzabile")
                value = str(value)
                if risk_level not in ("low", "medium", "high"):
                    risk_level = "low"
            except (OpenAINotConfiguredError, OpenAIRequestError):
                value, reasoning, risk_level = _rules_metafield(metafield_row, entity)
        else:
            if use_ai and not is_openai_configured():
                raise ValueError("AI non configurata")
            value, reasoning, risk_level = _rules_metafield(metafield_row, entity)

        return {
            "field": field,
            "value": value,
            "reasoning": reasoning,
            "risk_level": risk_level,
            "metafield_id": str(metafield_row.id),
        }

    if use_ai and is_openai_configured():
        system_prompt = _ai_system_prompt(skill_ctx.as_proposal_prompt_context())
        user_prompt = _ai_field_user_prompt(
            entity_type=entity_type,
            field=field,
            snake_field=snake_field,
            current=current,
            analysis=analysis,
            image_id=image_id,
        )
        try:
            result = await generate_structured_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            value = result.get("value")
            reasoning = str(result.get("reasoning") or "")
            risk_level = str(result.get("risk_level") or "low")
            if value is None or (isinstance(value, str) and not value.strip()):
                raise OpenAIRequestError("Risposta AI senza valore utilizzabile")
            if field == "imageAlt" and entity_type == "product":
                if isinstance(value, str):
                    value = {
                        "image_id": image_id,
                        "proposed_alt": value,
                        "reason": reasoning,
                    }
                elif isinstance(value, dict):
                    value.setdefault("image_id", image_id)
            if risk_level not in ("low", "medium", "high"):
                risk_level = "low"
        except (OpenAINotConfiguredError, OpenAIRequestError):
            value, reasoning, risk_level = _rules_single_field(
                entity_type, field, entity, analysis, current, image_id
            )
    else:
        if use_ai and not is_openai_configured():
            raise ValueError("AI non configurata")
        value, reasoning, risk_level = _rules_single_field(
            entity_type, field, entity, analysis, current, image_id
        )

    return {
        "field": field,
        "value": value,
        "reasoning": reasoning,
        "risk_level": risk_level,
    }
