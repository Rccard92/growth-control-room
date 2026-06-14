"""Tests for AI model settings service and routing insights schema."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.api.routes.ai_model_settings import (
    _normalize_setting_item,
    _to_list_response,
    update_project_ai_model_setting,
)
from app.api.validation_helpers import is_json_string_body_validation_error
from app.schemas.ai_model_settings import (
    AiAvailableModelItem,
    AiModelSettingItemResponse,
    AiModelSettingUpdateRequest,
)
from app.schemas.ai_usage import AiRoutingInsights
from app.services.ai.model_settings_service import (
    apply_gcr_recommendations,
    compute_guardrail_warnings,
    get_available_models,
    list_settings_for_project,
    seed_default_settings,
    validate_model_for_operation,
)
from app.services.ai.operation_registry import get_operation, tier_cost_profile_label
from app.services.ai.pricing import estimate_usage_cost


def _sample_snake_item(**overrides: object) -> dict:
    base = {
        "operation_key": "product_image_alt",
        "label": "Alt immagine prodotto",
        "status": "implemented",
        "enabled": True,
        "module": "product_seo",
        "context_profile": "image_alt",
        "recommended_tier": "cheap",
        "recommended_model": "gpt-4o-mini",
        "recommended_max_output_tokens": 120,
        "recommended_temperature": 0.3,
        "recommended_use": "Alt brevi",
        "quality_level": "low",
        "cost_sensitivity": "high",
        "description": "Alt testo immagine",
        "warning_notes": None,
        "model": "gpt-4o-mini",
        "model_tier": "cheap",
        "max_output_tokens": 120,
        "temperature": 0.3,
        "fallback_model": "gpt-4o-mini",
        "allow_fallback": True,
        "reasoning_effort": None,
        "notes": None,
        "source": "env_seed",
        "has_project_override": False,
        "guardrail_warnings": [],
        "recent_request_count": 0,
        "avg_cost_recent": None,
        "last_request_at": None,
        "ui_category": "product_collection_seo",
        "gcr_recommended_model": "gpt-5.4-mini",
        "gcr_recommendation_reason": "Usa un modello leggero: è un task breve e controllato.",
        "cost_profile_label": "profilo costo: leggero",
    }
    base.update(overrides)
    return base


def test_routing_insights_snake_case_validates() -> None:
    payload = {
        "cost_by_tier": {"cheap": 0.01},
        "requests_by_tier": {"cheap": 2},
        "premium_on_cheap_profile_count": 0,
        "explicit_override_count": 0,
        "unconfigured_model_warnings": [],
        "schema_fallback_retry_count": 0,
    }
    model = AiRoutingInsights.model_validate(payload)
    dumped = model.model_dump(by_alias=True)
    assert dumped["costByTier"]["cheap"] == 0.01
    assert dumped["requestsByTier"]["cheap"] == 2


def test_setting_item_snake_case_validates() -> None:
    item = AiModelSettingItemResponse.model_validate(_sample_snake_item())
    dumped = item.model_dump(by_alias=True)
    assert dumped["operationKey"] == "product_image_alt"
    assert dumped["modelTier"] == "cheap"


def test_setting_item_camel_case_normalizes() -> None:
    camel = {
        "operationKey": "blog_brief_generation",
        "label": "Brief editoriale",
        "status": "implemented",
        "enabled": True,
        "module": "blog_brief",
        "contextProfile": "blog_brief",
        "recommendedTier": "standard",
        "recommendedModel": "gpt-4o-mini",
        "recommendedMaxOutputTokens": 3000,
        "recommendedTemperature": 0.5,
        "recommendedUse": "Brief",
        "qualityLevel": "high",
        "costSensitivity": "medium",
        "description": "Brief",
        "model": "gpt-4o-mini",
        "modelTier": "standard",
        "allowFallback": True,
        "source": "manual",
        "hasProjectOverride": True,
        "guardrailWarnings": [],
        "recentRequestCount": 2,
        "uiCategory": "blog_articles",
        "gcrRecommendedModel": "gpt-5.4",
        "gcrRecommendationReason": "Brief strutturato.",
        "costProfileLabel": "profilo costo: bilanciato",
    }
    normalized = _normalize_setting_item(camel)
    item = AiModelSettingItemResponse.model_validate(normalized)
    assert item.operation_key == "blog_brief_generation"
    assert item.recent_request_count == 2


def test_to_list_response_no_validation_error() -> None:
    data = {
        "items": [_sample_snake_item()],
        "registry_count": 40,
        "missing_settings": [],
        "available_models": {
            "env_models": {"cheap": "gpt-4o-mini"},
            "models": [{"name": "gpt-4o-mini", "pricing_configured": True, "source": "env"}],
            "warnings": [],
        },
        "unpriced_models": [],
    }
    response = _to_list_response(data)
    assert len(response.items) == 1
    assert response.items[0].operation_key == "product_image_alt"
    dumped = response.model_dump(by_alias=True)
    assert dumped["items"][0]["operationKey"] == "product_image_alt"


def test_to_list_response_camel_case_payload() -> None:
    data = {
        "items": [
            {
                "operationKey": "product_image_alt",
                "label": "Alt",
                "status": "implemented",
                "enabled": True,
                "module": "product_seo",
                "contextProfile": "image_alt",
                "recommendedTier": "cheap",
                "recommendedModel": "gpt-4o-mini",
                "recommendedMaxOutputTokens": 120,
                "recommendedTemperature": 0.3,
                "recommendedUse": "Alt",
                "qualityLevel": "low",
                "costSensitivity": "high",
                "description": "d",
                "model": "gpt-4o-mini",
                "modelTier": "cheap",
                "allowFallback": True,
                "source": "env_seed",
                "hasProjectOverride": False,
                "guardrailWarnings": [],
                "recentRequestCount": 0,
                "uiCategory": "product_collection_seo",
                "gcrRecommendedModel": "gpt-5.4-mini",
                "gcrRecommendationReason": "Task breve.",
                "costProfileLabel": "profilo costo: leggero",
            }
        ],
        "registryCount": 1,
        "missingSettings": [],
        "availableModels": {
            "envModels": {"cheap": "gpt-4o-mini"},
            "models": [{"name": "gpt-4o-mini", "pricingConfigured": True, "source": "env"}],
            "warnings": [],
        },
    }
    response = _to_list_response(data)
    assert response.registry_count == 1
    assert response.items[0].model == "gpt-4o-mini"


def test_planned_operation_null_model() -> None:
    item = AiModelSettingItemResponse.model_validate(
        _sample_snake_item(
            operation_key="collection_image_alt",
            label="Alt collection",
            status="planned",
            enabled=False,
            model=None,
            model_tier="cheap",
            guardrail_warnings=["Operazione pianificata — nessun modello attivo."],
        )
    )
    assert item.model is None
    assert item.status == "planned"


def test_non_ai_operation_no_crash() -> None:
    op = get_operation("editorial_plan_generation")
    assert op is not None
    assert op.status == "non_ai"
    item = AiModelSettingItemResponse.model_validate(
        _sample_snake_item(
            operation_key=op.operation_key,
            label=op.label,
            status="non_ai",
            enabled=False,
            model=None,
            module=op.module,
            context_profile=op.context_profile,
            recommended_tier=op.recommended_tier,
            recommended_max_output_tokens=op.recommended_max_output_tokens,
            recommended_temperature=op.recommended_temperature,
            recommended_use=op.recommended_use,
            quality_level=op.quality_level,
            cost_sensitivity=op.cost_sensitivity,
            description=op.description,
            guardrail_warnings=["Operazione non AI — nessun modello configurato."],
        )
    )
    assert item.status == "non_ai"


def test_available_models_snake_case() -> None:
    model = AiAvailableModelItem.model_validate(
        {
            "name": "gpt-4o-mini",
            "pricing_configured": True,
            "source": "env",
            "family": "legacy_chat",
            "known_supported": True,
        }
    )
    assert model.pricing_configured is True
    assert model.known_supported is True


def test_critical_operation_cheap_warning() -> None:
    op = get_operation("article_draft_generation")
    assert op is not None
    warnings = compute_guardrail_warnings(op, model_tier="cheap", model_name="gpt-4o-mini")
    assert any("critica" in w for w in warnings)


def test_planned_operation_guardrail_message() -> None:
    op = get_operation("collection_image_alt")
    assert op is not None
    warnings = compute_guardrail_warnings(op, model_tier="cheap", model_name=None)
    assert any("pianificata" in w.lower() for w in warnings)


def test_unknown_model_not_in_guardrail_warnings() -> None:
    op = get_operation("product_image_alt")
    assert op is not None
    warnings = compute_guardrail_warnings(op, model_tier="cheap", model_name="unknown-model-xyz-999")
    assert not any("pricing" in w.lower() for w in warnings)


def test_gpt5_pricing_configured() -> None:
    assert estimate_usage_cost("gpt-5.5", input_tokens=100, output_tokens=50) is not None
    assert estimate_usage_cost("gpt-5.4-mini", input_tokens=100, output_tokens=50) is not None


def test_registry_gcr_recommendations() -> None:
    alt = get_operation("product_image_alt")
    article = get_operation("article_draft_generation")
    assert alt is not None and article is not None
    assert alt.gcr_recommended_model == "gpt-5.4-mini"
    assert article.gcr_recommended_model == "gpt-5.5"
    assert alt.ui_category == "product_collection_seo"
    assert tier_cost_profile_label("cheap") == "profilo costo: leggero"


def test_apply_gcr_recommendations_updates_implemented() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        session.flush = AsyncMock()
        session.add = MagicMock()

        row = MagicMock()
        row.model = "old-model"
        row.source = "env_seed"

        session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=row))
        )

        updated = await apply_gcr_recommendations(session, project_id)
        assert updated > 0
        assert row.model != "old-model"
        assert row.source == "manual"

    asyncio.run(run())


def test_list_settings_includes_gcr_fields() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        session.flush = AsyncMock()

        empty_scalars = MagicMock()
        empty_scalars.all.return_value = []
        empty_result = MagicMock()
        empty_result.scalars.return_value = empty_scalars
        empty_result.scalar_one_or_none.return_value = None
        empty_result.one.return_value = (0, None, None)

        session.execute = AsyncMock(return_value=empty_result)

        data = await list_settings_for_project(session, project_id)
        alt = next(i for i in data["items"] if i["operation_key"] == "product_image_alt")
        assert alt["gcr_recommended_model"] == "gpt-5.4-mini"
        assert alt["ui_category"] == "product_collection_seo"
        assert "unpriced_models" in data

    asyncio.run(run())


def test_seed_default_settings_creates_rows() -> None:
    async def run() -> None:
        session = AsyncMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        session.flush = AsyncMock()
        created = await seed_default_settings(session, project_id=None, source="env_seed")
        assert created > 0
        assert session.add.call_count == created

    asyncio.run(run())


def test_list_settings_empty_db_mock() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        session.flush = AsyncMock()

        empty_scalars = MagicMock()
        empty_scalars.all.return_value = []
        empty_result = MagicMock()
        empty_result.scalars.return_value = empty_scalars
        empty_result.scalar_one_or_none.return_value = None
        empty_result.one.return_value = (0, None, None)

        session.execute = AsyncMock(return_value=empty_result)

        data = await list_settings_for_project(session, project_id)
        assert "items" in data
        assert len(data["items"]) > 0
        first = data["items"][0]
        assert "operation_key" in first
        assert "context_profile" in first
        assert "model_tier" in first
        assert "recommended_tier" in first

    asyncio.run(run())


def test_get_available_models_snake_case() -> None:
    async def run() -> None:
        session = AsyncMock()
        log_scalars = MagicMock()
        log_scalars.all.return_value = []
        session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=log_scalars))
        )
        data = await get_available_models(session)
        assert "env_models" in data
        assert "pricing_configured" in data["models"][0]

    asyncio.run(run())


def test_update_request_accepts_object_body() -> None:
    request = AiModelSettingUpdateRequest.model_validate({"model": "gpt-5.4-mini"})
    assert request.model == "gpt-5.4-mini"


def test_put_ai_model_setting_object_returns_200() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        session.commit = AsyncMock()

        row = MagicMock()
        row.model = "gpt-5.4-mini"
        row.model_tier = "cheap"
        row.source = "manual"

        with (
            patch(
                "app.api.routes.ai_model_settings.get_project_in_default_workspace",
                new_callable=AsyncMock,
            ),
            patch(
                "app.api.routes.ai_model_settings.update_project_setting",
                new_callable=AsyncMock,
                return_value=row,
            ) as mock_update,
        ):
            result = await update_project_ai_model_setting(
                project_id,
                "product_image_alt",
                AiModelSettingUpdateRequest(model="gpt-5.4-mini"),
                session=session,
            )

        assert result.model == "gpt-5.4-mini"
        assert result.operation_key == "product_image_alt"
        mock_update.assert_awaited_once()
        session.commit.assert_awaited_once()

    asyncio.run(run())


def test_put_ai_model_setting_string_body_returns_422() -> None:
    errors = [
        {
            "type": "model_attributes_type",
            "loc": ("body",),
            "msg": "Input should be a valid dictionary or object to extract fields from",
            "input": '{"model":"gpt-5.4-mini"}',
        }
    ]
    assert is_json_string_body_validation_error(errors) is True


def test_update_request_rejects_string_body() -> None:
    from pydantic import ValidationError

    try:
        AiModelSettingUpdateRequest.model_validate('{"model":"gpt-5.4-mini"}')
        raise AssertionError("expected ValidationError")
    except ValidationError:
        pass


def test_validate_model_local_compatible() -> None:
    async def run() -> None:
        project_id = uuid4()
        session = AsyncMock()
        with patch(
            "app.services.ai.ai_client.is_openai_configured",
            return_value=False,
        ):
            data = await validate_model_for_operation(
                session,
                project_id,
                model="gpt-5.4-mini",
                operation_key="product_image_alt",
                run_probe=False,
            )
        assert data["compatible"] is True
        assert data["family"] == "reasoning"
        assert data["known_supported"] is True

    asyncio.run(run())


def test_get_available_models_includes_gpt5() -> None:
    async def run() -> None:
        session = AsyncMock()
        log_scalars = MagicMock()
        log_scalars.all.return_value = []
        session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=log_scalars))
        )
        data = await get_available_models(session)
        names = {m["name"] for m in data["models"]}
        assert "gpt-5.4-mini" in names
        gpt5 = next(m for m in data["models"] if m["name"] == "gpt-5.4-mini")
        assert gpt5["family"] == "reasoning"
        assert gpt5["known_supported"] is True

    asyncio.run(run())
