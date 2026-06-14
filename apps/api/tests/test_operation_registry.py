"""Tests for AI operation registry."""

from app.services.ai.operation_registry import (
    AI_OPERATIONS,
    get_operation,
    infer_operation_key,
    list_operations,
)


def test_registry_contains_core_operations() -> None:
    keys = {
        "brand_profile_enrichment",
        "product_image_alt",
        "blog_brief_generation",
        "article_draft_generation",
        "ped_strategy",
        "editorial_plan_generation",
    }
    for key in keys:
        assert key in AI_OPERATIONS


def test_planned_operations_disabled() -> None:
    op = get_operation("ped_strategy")
    assert op is not None
    assert op.status == "planned"
    assert op.enabled is False


def test_editorial_plan_non_ai() -> None:
    op = get_operation("editorial_plan_generation")
    assert op is not None
    assert op.status == "non_ai"
    assert op.enabled is False


def test_infer_product_image_alt() -> None:
    key = infer_operation_key(
        "product_seo",
        "generate_field",
        "image_alt",
        "product_image",
    )
    assert key == "product_image_alt"


def test_list_operations_includes_planned() -> None:
    assert len(list_operations(include_planned=True)) >= len(list_operations(include_planned=False))
