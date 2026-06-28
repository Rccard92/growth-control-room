"""Build high-quality editorial hero image prompts for Solmielato brand."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.content.editorial_image_processing import (
    EDITORIAL_IMAGE_FINAL_SIZE,
    EDITORIAL_IMAGE_PROVIDER_SIZE,
)

NEGATIVE_CONSTRAINTS = (
    "No text inside the image, no letters, no watermark, no graphic overlay, "
    "no invented logos, no fake readable labels, no stock-artificial look, "
    "no oversaturated colors, no cluttered scenes, no people, no hands, no faces, "
    "no medical or health claims."
)

BRAND_VISUAL_GUIDE = (
    "Artisanal Italian organic honey brand, premium but natural, Mediterranean aesthetic, "
    "warm yet clean editorial food/lifestyle mood. Palette: honey gold, cream white, natural beige, "
    "light wood, pale ceramic, linen, light stone, subtle botanical green accents. "
    "Soft natural light, gentle shadows, authentic magazine editorial quality."
)


@dataclass(frozen=True)
class EditorialImagePromptContext:
    content_type: str
    article_title: str
    article_excerpt: str
    article_body_excerpt: str
    primary_keyword: str
    secondary_keywords: list[str]
    search_intent: str
    target_audience: str
    content_angle: str
    linked_products: list[str]
    linked_collections: list[str]
    brand_context: str | None
    skill_context: str
    revision_note: str | None = None
    previous_prompt: str | None = None


def resolve_content_type_hints(content_type: str) -> str:
    normalized = (content_type or "").strip().lower()
    hints: dict[str, str] = {
        "recipe": (
            "Recipe content: the dish is the hero. Show realistic premium food photography with "
            "ingredients coherent with the recipe. Honey must be visible as an important ingredient "
            "(drizzle, honey dipper, or small clear glass jar with label turned away). "
            "Natural breakfast or everyday scene when appropriate."
        ),
        "educational_article": (
            "Educational content: editorial still life with honey as protagonist or co-protagonist. "
            "Evocative but clear magazine editorial look. Simple natural context, no infographic text."
        ),
        "product_guide": (
            "Product guide: focus on honey usage or variety. Elegant table setting, breakfast, "
            "tasting or descriptive still life. Premium but approachable."
        ),
        "brand_storytelling": (
            "Brand storytelling: warm authentic atmosphere, strong Solmielato world coherence, "
            "realistic visual storytelling without staged stock look."
        ),
        "seasonal_article": (
            "Seasonal content: visual seasonality coherent with title and keywords. "
            "Natural editorial still life with honey and seasonal elements."
        ),
        "faq_objection_article": (
            "FAQ/objection content: clear evocative still life, honey and relevant context, "
            "simple composition without confusion."
        ),
        "product_comparison": (
            "Product comparison content: elegant still life suggesting variety or usage context, "
            "clean editorial layout, no text or charts in image."
        ),
    }
    if normalized in hints:
        return hints[normalized]
    return (
        "Editorial hero image aligned with article title and keywords. "
        "Honey as natural focal point when relevant. Clean premium food/lifestyle editorial look."
    )


def build_editorial_image_prompt_system(ctx: EditorialImagePromptContext) -> str:
    base = (
        "You are an art director for a premium Italian organic honey Shopify blog (Solmielato). "
        "Generate a single detailed image prompt in English for an editorial hero image. "
        f"Landscape 3:2, provider generation size {EDITORIAL_IMAGE_PROVIDER_SIZE}, "
        f"final output {EDITORIAL_IMAGE_FINAL_SIZE} JPG. "
        "Describe subject, composition, lighting, materials, mood, and color palette. "
        "The prompt must feel like premium magazine food/lifestyle photography, never generic stock. "
        f"{BRAND_VISUAL_GUIDE} "
        f"Always include these negative constraints: {NEGATIVE_CONSTRAINTS} "
        "Respect Safe Claims and brand visual identity. "
        "Respond ONLY with valid JSON.\n\n"
        f"{ctx.skill_context}"
    )
    if ctx.brand_context:
        base += f"\n\nBrand and editorial context:\n{ctx.brand_context}"
    return base


def build_editorial_image_prompt_user(ctx: EditorialImagePromptContext) -> str:
    secondary = ", ".join(ctx.secondary_keywords[:8]) or "—"
    products = ", ".join(ctx.linked_products[:5]) or "—"
    collections = ", ".join(ctx.linked_collections[:5]) or "—"
    content_hints = resolve_content_type_hints(ctx.content_type)

    parts = [
        f"Create imagePrompt for Shopify blog hero image, landscape 3:2, final {EDITORIAL_IMAGE_FINAL_SIZE}.",
        f"Content type: {ctx.content_type or '—'}",
        f"Primary keyword: {ctx.primary_keyword or '—'}",
        f"Secondary keywords: {secondary}",
        f"Search intent: {ctx.search_intent or '—'}",
        f"Target audience: {ctx.target_audience or '—'}",
        f"Content angle: {ctx.content_angle or '—'}",
        f"Article title: {ctx.article_title}",
        f"Article excerpt: {ctx.article_excerpt[:400] if ctx.article_excerpt else '—'}",
        f"Article body excerpt: {ctx.article_body_excerpt[:600] if ctx.article_body_excerpt else '—'}",
        f"Linked products: {products}",
        f"Linked collections: {collections}",
        f"\nVisual direction for this content type:\n{content_hints}",
    ]

    if ctx.previous_prompt and ctx.revision_note:
        parts.extend(
            [
                f"\nPrevious image prompt:\n{ctx.previous_prompt}",
                f"\nUser edit instructions:\n{ctx.revision_note.strip()}",
                "Revise the prompt accordingly while keeping Solmielato brand rules.",
            ]
        )
    elif ctx.revision_note:
        parts.append(f"\nUser edit instructions:\n{ctx.revision_note.strip()}")

    parts.append('\nRespond with JSON: {"imagePrompt":"..."}')
    return "\n".join(parts)
