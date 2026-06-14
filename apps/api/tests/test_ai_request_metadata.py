"""Tests for AiRequestMetadata ID coercion (UUID/int → str)."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.services.ai.ai_client import AiRequestMetadata


def _base_kwargs(project_id: UUID) -> dict:
    return {
        "project_id": project_id,
        "module": "content_seo",
        "operation": "seo_proposal_field",
        "entity_type": "product",
    }


def test_entity_id_uuid_coerced_to_string() -> None:
    project_id = uuid4()
    entity_id = uuid4()
    metadata = AiRequestMetadata(**_base_kwargs(project_id), entity_id=entity_id)
    assert metadata.entity_id == str(entity_id)
    assert isinstance(metadata.entity_id, str)


def test_job_id_uuid_coerced_to_string() -> None:
    project_id = uuid4()
    job_id = uuid4()
    metadata = AiRequestMetadata(**_base_kwargs(project_id), job_id=job_id)
    assert metadata.job_id == str(job_id)
    assert isinstance(metadata.job_id, str)


def test_entity_id_int_coerced_to_string() -> None:
    project_id = uuid4()
    metadata = AiRequestMetadata(**_base_kwargs(project_id), entity_id=12345)
    assert metadata.entity_id == "12345"


def test_project_id_uuid_unchanged() -> None:
    project_id = uuid4()
    metadata = AiRequestMetadata(**_base_kwargs(project_id))
    assert metadata.project_id == project_id
    assert isinstance(metadata.project_id, UUID)


def test_project_id_string_coerced_to_uuid() -> None:
    project_id = uuid4()
    metadata = AiRequestMetadata(**_base_kwargs(str(project_id)))
    assert metadata.project_id == project_id
    assert isinstance(metadata.project_id, UUID)


def test_entity_id_none_allowed() -> None:
    project_id = uuid4()
    metadata = AiRequestMetadata(**_base_kwargs(project_id), entity_id=None)
    assert metadata.entity_id is None


def test_seo_field_engine_metadata_pattern_no_validation_error() -> None:
    """Same construction pattern as seo_proposal_field_engine."""
    project_id = uuid4()
    product_id = uuid4()
    metadata = AiRequestMetadata(
        project_id=project_id,
        module="content_seo",
        operation="seo_proposal_field",
        entity_type="product",
        entity_id=product_id,
        operation_key="content_seo.product_seo_field",
        context_profile="content_seo_product_field",
    )
    assert metadata.entity_id == str(product_id)
