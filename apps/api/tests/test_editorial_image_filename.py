"""Tests for editorial image SEO filename generation."""

from app.services.content.editorial_image_filename import (
    FALLBACK_FILENAME,
    build_editorial_image_filename,
    resolve_unique_editorial_image_filename,
)


def test_slug_from_title_with_accents_and_punctuation() -> None:
    title = "Yogurt con frutta, noci e miele: una ricetta semplice per ogni giorno"
    filename = build_editorial_image_filename(title)
    assert filename == (
        "yogurt-con-frutta-noci-e-miele-una-ricetta-semplice-per-ogni-giorno.jpg"
    )


def test_fallback_filename_when_empty() -> None:
    assert build_editorial_image_filename("   ") == FALLBACK_FILENAME


def test_max_length_90_chars_before_extension() -> None:
    title = "A" * 120
    filename = build_editorial_image_filename(title)
    assert filename.endswith(".jpg")
    assert len(filename) - 4 <= 90


def test_forbidden_patterns_use_fallback() -> None:
    assert build_editorial_image_filename("ChatGPT generated image") == FALLBACK_FILENAME


def test_collision_suffix_version() -> None:
    title = "Guida al miele"
    base = build_editorial_image_filename(title)
    existing = {base}
    unique = resolve_unique_editorial_image_filename(title, existing_filenames=existing)
    assert unique == "guida-al-miele-v2.jpg"


def test_collision_with_short_hash() -> None:
    title = "Guida al miele"
    base = build_editorial_image_filename(title)
    existing = {base, "guida-al-miele-v2.jpg"}
    unique = resolve_unique_editorial_image_filename(
        title,
        existing_filenames=existing,
        version_hint="test",
    )
    assert unique.endswith(".jpg")
    assert unique not in existing
