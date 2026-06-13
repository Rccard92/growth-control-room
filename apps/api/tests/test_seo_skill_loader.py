"""Tests for SEO skill loader."""

from app.services.content.seo_skill_loader import (
    GCR_SKILL_DIR,
    EXTERNAL_SKILL_DIR,
    clear_seo_skill_cache,
    get_seo_skill_metadata,
    load_external_skill_references,
    load_seo_skill_context,
)


def setup_function() -> None:
    clear_seo_skill_cache()


def test_load_gcr_skill_context_all_fields() -> None:
    ctx = load_seo_skill_context()
    assert ctx.skill
    assert ctx.product_rules
    assert ctx.collection_rules
    assert ctx.image_alt_rules
    assert ctx.proposal_rules
    assert ctx.content_brief_rules
    assert ctx.schema_rules
    assert ctx.brand_guardrails
    assert ctx.source_map
    assert ctx.version == "1.0.0"
    assert ctx.loaded_from_files is True


def test_gcr_skill_dir_exists() -> None:
    assert GCR_SKILL_DIR.is_dir()
    assert (GCR_SKILL_DIR / "SKILL.md").exists()
    assert (GCR_SKILL_DIR / "product-seo-rules.md").exists()


def test_external_references_loaded() -> None:
    refs = load_external_skill_references()
    assert len(refs) >= 4
    assert any("seo-ecommerce" in ref for ref in refs)
    assert any("seo-images" in ref for ref in refs)


def test_external_skill_dir_exists() -> None:
    assert EXTERNAL_SKILL_DIR.is_dir()
    assert (EXTERNAL_SKILL_DIR / "seo-ecommerce" / "SKILL.md").exists()


def test_get_seo_skill_metadata() -> None:
    meta = get_seo_skill_metadata()
    d = meta.to_dict()
    assert d["name"] == "GCR Shopify SEO Skill"
    assert d["version"] == "1.0.0"
    assert "claude-seo" in d["attribution"]
    assert len(d["score_rule_categories"]) == 7
    assert len(d["external_skills"]) >= 4


def test_proposal_prompt_context_includes_rules() -> None:
    ctx = load_seo_skill_context()
    prompt = ctx.as_proposal_prompt_context()
    assert "# Product rules" in prompt
    assert "# Collection rules" in prompt
    assert "# Image alt rules" in prompt
    assert "# Proposal rules" in prompt
    assert "# Brand guardrails" in prompt
    assert "# Source map (summary)" in prompt
    assert len(prompt) < 50000
