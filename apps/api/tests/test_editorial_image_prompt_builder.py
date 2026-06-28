"""Tests for editorial image prompt builder."""

from app.services.content.editorial_image_prompt_builder import (
    BRAND_VISUAL_GUIDE,
    NEGATIVE_CONSTRAINTS,
    EditorialImagePromptContext,
    build_editorial_image_prompt_system,
    build_editorial_image_prompt_user,
    resolve_content_type_hints,
)


def _ctx(content_type: str = "recipe", **overrides: object) -> EditorialImagePromptContext:
    base = EditorialImagePromptContext(
        content_type=content_type,
        article_title="Yogurt con frutta, noci e miele",
        article_excerpt="Ricetta semplice per ogni giorno.",
        article_body_excerpt="Yogurt cremoso con frutta fresca, noci e miele.",
        primary_keyword="yogurt miele",
        secondary_keywords=["colazione", "ricetta facile"],
        search_intent="informational",
        target_audience="famiglie",
        content_angle="everyday breakfast",
        linked_products=["Miele di acacia"],
        linked_collections=[],
        brand_context="Solmielato organic honey brand",
        skill_context="# Editorial image skill",
    )
    data = base.__dict__.copy()
    data.update(overrides)
    return EditorialImagePromptContext(**data)


def test_recipe_hints_include_food_photography() -> None:
    hints = resolve_content_type_hints("recipe")
    assert "food photography" in hints.lower() or "dish" in hints.lower()
    assert "honey" in hints.lower()


def test_educational_article_hints() -> None:
    hints = resolve_content_type_hints("educational_article")
    assert "still life" in hints.lower()
    assert "honey" in hints.lower()


def test_product_guide_hints() -> None:
    hints = resolve_content_type_hints("product_guide")
    assert "honey" in hints.lower()


def test_brand_storytelling_hints() -> None:
    hints = resolve_content_type_hints("brand_storytelling")
    assert "authentic" in hints.lower() or "storytelling" in hints.lower()


def test_system_prompt_includes_brand_and_negatives() -> None:
    system = build_editorial_image_prompt_system(_ctx())
    assert "1200x800" in system
    assert "3:2" in system
    assert BRAND_VISUAL_GUIDE.split()[0] in system
    assert "No text inside the image" in NEGATIVE_CONSTRAINTS
    assert "No text inside the image" in system


def test_user_prompt_includes_article_context() -> None:
    user = build_editorial_image_prompt_user(_ctx())
    assert "Yogurt con frutta, noci e miele" in user
    assert "yogurt miele" in user
    assert "Miele di acacia" in user
    assert "recipe" in user.lower() or "Recipe content" in user


def test_user_prompt_includes_revision_note() -> None:
    user = build_editorial_image_prompt_user(
        _ctx(
            revision_note="More natural light, focus on honey drizzle",
            previous_prompt="Previous prompt about yogurt bowl",
        )
    )
    assert "More natural light" in user
    assert "Previous prompt about yogurt bowl" in user
