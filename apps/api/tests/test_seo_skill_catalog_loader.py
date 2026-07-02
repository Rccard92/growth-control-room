"""Tests for SEO skill catalog loader."""

from app.services.seo_skills.catalog_loader import (
    CATALOG_PATH,
    _build_counts,
    clear_seo_skill_catalog_cache,
    get_seo_skill_by_key,
    list_available_seo_skills,
    load_seo_skill_catalog,
)

REQUIRED_SKILL_KEYS = {
    "seo_audit",
    "seo_page",
    "seo_technical",
    "seo_content",
    "seo_content_brief",
    "seo_schema",
    "seo_geo",
    "seo_images",
    "seo_sitemap_analyze",
    "seo_sitemap_generate",
    "seo_plan",
    "seo_competitor_pages",
    "seo_hreflang",
    "seo_programmatic",
    "seo_local",
    "seo_maps",
    "seo_backlinks",
    "seo_cluster",
    "seo_sxo",
    "seo_drift_baseline",
    "seo_drift_compare",
    "seo_ecommerce",
    "seo_flow",
    "seo_google",
    "seo_image_gen",
    "seo_firecrawl",
    "seo_dataforseo",
}


def setup_function() -> None:
    clear_seo_skill_catalog_cache()


def test_catalog_path_exists() -> None:
    assert CATALOG_PATH.is_file()


def test_load_seo_skill_catalog_loads_all_skills() -> None:
    skills = load_seo_skill_catalog()
    assert len(skills) == len(REQUIRED_SKILL_KEYS)


def test_required_skill_keys_present() -> None:
    skills = load_seo_skill_catalog()
    keys = {skill.key for skill in skills}
    assert REQUIRED_SKILL_KEYS.issubset(keys)
    assert "seo_geo" in keys
    assert "seo_firecrawl" in keys
    assert "seo_dataforseo" in keys


def test_list_available_seo_skills_excludes_non_available() -> None:
    available = list_available_seo_skills()
    available_keys = {skill.key for skill in available}
    assert "seo_audit" in available_keys
    assert "seo_ecommerce" in available_keys
    assert "seo_firecrawl" not in available_keys
    assert "seo_dataforseo" not in available_keys
    assert "seo_google" not in available_keys
    assert all(skill.status == "available" and skill.enabled for skill in available)


def test_get_seo_skill_by_key_returns_item() -> None:
    skill = get_seo_skill_by_key("seo_ecommerce")
    assert skill is not None
    assert skill.key == "seo_ecommerce"
    assert skill.category == "ecommerce"


def test_get_seo_skill_by_key_missing_returns_none() -> None:
    assert get_seo_skill_by_key("seo_nonexistent") is None


def test_needs_config_and_external_required_remain_in_full_catalog() -> None:
    skills = load_seo_skill_catalog()
    by_key = {skill.key: skill for skill in skills}
    assert by_key["seo_competitor_pages"].status == "needs_config"
    assert by_key["seo_firecrawl"].status == "external_required"
    assert by_key["seo_backlinks"].status == "external_required"


def test_cache_clear_reloads_catalog() -> None:
    first = load_seo_skill_catalog()
    clear_seo_skill_catalog_cache()
    second = load_seo_skill_catalog()
    assert len(first) == len(second)


def test_build_counts() -> None:
    skills = load_seo_skill_catalog()
    counts = _build_counts(skills)
    assert counts.total == len(skills)
    assert counts.available == sum(1 for skill in skills if skill.status == "available")
    assert counts.needs_config == sum(
        1 for skill in skills if skill.status == "needs_config"
    )
    assert counts.external_required == sum(
        1 for skill in skills if skill.status == "external_required"
    )
    assert counts.planned == sum(1 for skill in skills if skill.status == "planned")
