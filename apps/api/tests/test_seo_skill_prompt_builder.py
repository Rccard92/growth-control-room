"""Tests for SEO skill prompt builder."""

from __future__ import annotations

from uuid import uuid4

from app.services.seo_skills.catalog_loader import get_seo_skill_by_key
from app.services.seo_skills.prompt_builder import (
    MAX_PROMPT_HTML_CHARS,
    MAX_PROMPT_TEXT_CHARS,
    build_skill_system_prompt,
    build_skill_user_prompt,
    mask_sensitive_values,
)


def _skill_input(**overrides: object) -> dict:
    base = {
        "projectId": str(uuid4()),
        "targetType": "url",
        "targetId": "",
        "url": "https://example.com/product",
        "title": "Scarpe Running Pro",
        "html": "<h1>Scarpe Running Pro</h1><p>Descrizione prodotto.</p>",
        "text": "Scarpe Running Pro. Descrizione prodotto.",
        "metadata": {"metaDescription": "Scarpe da running", "h1": ["Scarpe Running Pro"]},
        "shopify": {"product": {"title": "Scarpe Running Pro", "handle": "scarpe-running-pro"}},
        "brandContext": "Tono friendly, focus performance.",
        "warnings": ["Brand context parziale."],
    }
    base.update(overrides)
    return base


def _require_skill(key: str):
    skill = get_seo_skill_by_key(key)
    assert skill is not None, f"Skill {key} not found in catalog"
    return skill


def test_build_skill_system_prompt_contains_skill_key_and_label() -> None:
    skill = _require_skill("seo_schema")
    prompt = build_skill_system_prompt(skill, _skill_input())

    assert "seo_schema" in prompt
    assert skill.label in prompt


def test_build_skill_system_prompt_requires_json_only() -> None:
    skill = _require_skill("seo_schema")
    prompt = build_skill_system_prompt(skill, _skill_input())

    assert "SOLO JSON valido" in prompt
    assert "Non usare markdown fuori dal JSON" in prompt
    assert "JSON compatto" in prompt
    assert "Non superare 6 findings" in prompt
    assert "Non superare 6 recommendations" in prompt
    assert "Non superare 8 tasks" in prompt


def test_build_skill_system_prompt_includes_output_schema() -> None:
    skill = _require_skill("seo_schema")
    prompt = build_skill_system_prompt(skill, _skill_input())

    assert "skillKey" in prompt
    assert "findings" in prompt
    assert "artifacts" in prompt


def test_seo_schema_system_prompt_contains_json_ld_instructions() -> None:
    skill = _require_skill("seo_schema")
    prompt = build_skill_system_prompt(skill, _skill_input())

    assert "JSON-LD" in prompt
    assert "Schema.org" in prompt


def test_seo_geo_system_prompt_contains_citability_instructions() -> None:
    skill = _require_skill("seo_geo")
    prompt = build_skill_system_prompt(skill, _skill_input())

    assert "citability" in prompt.lower() or "citab" in prompt.lower()
    assert "AI Search" in prompt or "GEO" in prompt


def test_seo_ecommerce_system_prompt_contains_ecommerce_focus() -> None:
    skill = _require_skill("seo_ecommerce")
    prompt = build_skill_system_prompt(skill, _skill_input())

    assert "product SEO" in prompt.lower() or "product" in prompt.lower()
    assert "collection" in prompt.lower()


def test_seo_images_system_prompt_contains_alt_text_instructions() -> None:
    skill = _require_skill("seo_images")
    prompt = build_skill_system_prompt(skill, _skill_input())

    assert "alt text" in prompt.lower()


def test_seo_sxo_system_prompt_contains_search_experience_instructions() -> None:
    skill = _require_skill("seo_sxo")
    prompt = build_skill_system_prompt(skill, _skill_input())

    assert "search experience" in prompt.lower()


def test_build_skill_user_prompt_contains_target_url_and_title() -> None:
    skill = _require_skill("seo_page")
    prompt = build_skill_user_prompt(skill, _skill_input())

    assert "Target type: url" in prompt
    assert "https://example.com/product" in prompt
    assert "Scarpe Running Pro" in prompt


def test_build_skill_user_prompt_includes_brand_context_when_present() -> None:
    skill = _require_skill("seo_page")
    prompt = build_skill_user_prompt(skill, _skill_input())

    assert "Brand context:" in prompt
    assert "Tono friendly" in prompt


def test_build_skill_user_prompt_includes_warnings_when_present() -> None:
    skill = _require_skill("seo_page")
    prompt = build_skill_user_prompt(skill, _skill_input())

    assert "Input warnings:" in prompt
    assert "Brand context parziale." in prompt


def test_build_skill_user_prompt_truncates_long_input() -> None:
    skill = _require_skill("seo_page")
    long_html = "x" * (MAX_PROMPT_HTML_CHARS + 500)
    long_text = "y" * (MAX_PROMPT_TEXT_CHARS + 500)
    prompt = build_skill_user_prompt(
        skill,
        _skill_input(html=long_html, text=long_text),
    )

    assert len(prompt) < len(long_html) + len(long_text)
    assert "..." in prompt


def test_mask_sensitive_values_redacts_api_key_and_token() -> None:
    masked = mask_sensitive_values(
        {
            "api_key": "sk-live-secret",
            "authorization": "Bearer abc.def.ghi",
            "notes": "token=super-secret-value",
            "title": "Safe title",
        }
    )

    assert masked["api_key"] == "[REDACTED]"
    assert masked["authorization"] == "[REDACTED]"
    assert "[REDACTED]" in masked["notes"]
    assert masked["title"] == "Safe title"


def test_build_skill_user_prompt_masks_sensitive_values() -> None:
    skill = _require_skill("seo_page")
    prompt = build_skill_user_prompt(
        skill,
        _skill_input(
            metadata={
                "api_key": "sk-live-secret",
                "description": "Bearer abc.def.ghi",
            }
        ),
    )

    assert "sk-live-secret" not in prompt
    assert "abc.def.ghi" not in prompt
    assert "[REDACTED]" in prompt
