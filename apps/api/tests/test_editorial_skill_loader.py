"""Tests for editorial skill loader."""

from app.services.content.editorial_skill_loader import (
    EDITORIAL_SKILL_DIR,
    EDITORIAL_SKILL_NAME,
    clear_editorial_skill_cache,
    load_editorial_skill_context,
)


def setup_function() -> None:
    clear_editorial_skill_cache()


def test_load_editorial_skill_context_all_fields() -> None:
    ctx = load_editorial_skill_context()
    assert ctx.readme
    assert ctx.article_structure_rules
    assert ctx.readability_rules
    assert ctx.neuromarketing_rules
    assert ctx.shopify_html_rules
    assert ctx.internal_linking_rules
    assert ctx.faq_format_rules
    assert ctx.source_map
    assert ctx.version == "v1"
    assert ctx.loaded_from_files is True


def test_editorial_skill_dir_exists() -> None:
    assert EDITORIAL_SKILL_DIR.is_dir()
    assert (EDITORIAL_SKILL_DIR / "README.md").exists()
    assert (EDITORIAL_SKILL_DIR / "shopify-html-rules.md").exists()


def test_brief_prompt_context_includes_rules() -> None:
    ctx = load_editorial_skill_context()
    text = ctx.as_brief_prompt_context()
    assert EDITORIAL_SKILL_NAME in text
    assert "Readability rules" in text
    assert "Neuromarketing rules" in text
    assert "FAQ format rules" in text


def test_article_prompt_context_includes_html_rules() -> None:
    ctx = load_editorial_skill_context()
    text = ctx.as_article_prompt_context()
    assert "Shopify HTML rules" in text
    assert "gcr-article-note" in text
