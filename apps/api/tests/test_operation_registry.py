"""Tests for AI operation registry."""

import pytest

from app.services.ai.operation_registry import (
    AI_OPERATIONS,
    get_operation,
    get_operation_key_for_seo_skill,
    infer_operation_key,
    list_operations,
)

CLAUDE_SEO_OPERATION_KEYS = {
    "claude_seo_audit",
    "claude_seo_page",
    "claude_seo_technical",
    "claude_seo_content",
    "claude_seo_content_brief",
    "claude_seo_schema",
    "claude_seo_geo",
    "claude_seo_images",
    "claude_seo_sitemap_analyze",
    "claude_seo_sitemap_generate",
    "claude_seo_plan",
    "claude_seo_competitor_pages",
    "claude_seo_hreflang",
    "claude_seo_programmatic",
    "claude_seo_cluster",
    "claude_seo_sxo",
    "claude_seo_ecommerce",
    "claude_seo_flow",
    "claude_seo_google",
    "claude_seo_firecrawl",
    "claude_seo_dataforseo",
    "claude_seo_backlinks",
    "claude_seo_local",
    "claude_seo_maps",
    "claude_seo_drift_baseline",
    "claude_seo_drift_compare",
    "claude_seo_image_gen",
}

CLAUDE_SEO_IMPLEMENTED_KEYS = {
    "claude_seo_audit",
    "claude_seo_page",
    "claude_seo_technical",
    "claude_seo_content",
    "claude_seo_content_brief",
    "claude_seo_schema",
    "claude_seo_geo",
    "claude_seo_images",
    "claude_seo_sitemap_analyze",
    "claude_seo_sitemap_generate",
    "claude_seo_plan",
    "claude_seo_competitor_pages",
    "claude_seo_hreflang",
    "claude_seo_programmatic",
    "claude_seo_cluster",
    "claude_seo_sxo",
    "claude_seo_ecommerce",
    "claude_seo_flow",
}

CLAUDE_SEO_PLANNED_KEYS = CLAUDE_SEO_OPERATION_KEYS - CLAUDE_SEO_IMPLEMENTED_KEYS


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


def test_registry_gcr_fields() -> None:
    op = get_operation("product_image_alt")
    assert op is not None
    assert op.gcr_recommended_model == "gpt-5.4-mini"
    assert op.gcr_recommendation_reason
    assert op.ui_category == "product_collection_seo"


def test_list_operations_includes_planned() -> None:
    assert len(list_operations(include_planned=True)) >= len(list_operations(include_planned=False))


def test_claude_seo_operations_registered() -> None:
    assert CLAUDE_SEO_OPERATION_KEYS.issubset(AI_OPERATIONS.keys())
    assert len(CLAUDE_SEO_OPERATION_KEYS) == 27


def test_claude_seo_implemented_operations() -> None:
    for key in CLAUDE_SEO_IMPLEMENTED_KEYS:
        op = get_operation(key)
        assert op is not None
        assert op.status == "implemented"
        assert op.enabled is True
        assert op.ui_category == "seo_advanced"
        assert op.recommended_tier != "cheap"
        assert op.context_profile == "seo_skill_audit"


def test_claude_seo_page_uses_standard_tokens() -> None:
    op = get_operation("claude_seo_page")
    assert op is not None
    assert op.recommended_tier == "standard"
    assert op.recommended_max_output_tokens == 6000
    assert op.recommended_temperature == 0.30


def test_claude_seo_planned_operations() -> None:
    assert len(CLAUDE_SEO_PLANNED_KEYS) == 9
    for key in CLAUDE_SEO_PLANNED_KEYS:
        op = get_operation(key)
        assert op is not None
        assert op.status == "planned"
        assert op.enabled is False
        assert op.warning_notes


def test_get_operation_key_for_seo_skill() -> None:
    assert get_operation_key_for_seo_skill("seo_geo") == "claude_seo_geo"
    assert get_operation_key_for_seo_skill("claude_seo_geo") == "claude_seo_geo"
    assert get_operation_key_for_seo_skill("seo_content_brief") == "claude_seo_content_brief"


def test_get_operation_key_for_unknown_skill() -> None:
    with pytest.raises(ValueError, match="Operazione SEO Skill non registrata"):
        get_operation_key_for_seo_skill("seo_unknown")


def test_get_operation_key_for_empty_skill() -> None:
    with pytest.raises(ValueError, match="skill_key vuoto"):
        get_operation_key_for_seo_skill("   ")


def test_existing_operations_unchanged() -> None:
    alt = get_operation("product_image_alt")
    brief = get_operation("blog_brief_generation")
    assert alt is not None
    assert brief is not None
    assert alt.status == "implemented"
    assert brief.status == "implemented"
    assert alt.recommended_tier == "cheap"
    assert brief.recommended_tier == "standard"


def test_list_operations_includes_claude_seo() -> None:
    keys = {op.operation_key for op in list_operations(include_planned=True)}
    assert "claude_seo_geo" in keys
    assert "claude_seo_firecrawl" in keys
