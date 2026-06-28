"""Tests for editorial image post-processing."""

import io

from PIL import Image

from app.services.content.editorial_image_processing import (
    TARGET_HEIGHT,
    TARGET_WIDTH,
    normalize_editorial_image_bytes,
)


def _make_image_bytes(width: int, height: int, color: str = "red") -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def test_normalize_square_to_1600x900() -> None:
    output, meta = normalize_editorial_image_bytes(_make_image_bytes(1024, 1024))
    with Image.open(io.BytesIO(output)) as img:
        assert img.size == (TARGET_WIDTH, TARGET_HEIGHT)
    assert meta["width"] == 1600
    assert meta["height"] == 900
    assert meta["aspect_ratio"] == "16:9"
    assert meta["mime_type"] == "image/jpeg"
    assert meta["extension"] == "jpg"


def test_normalize_landscape_3_2_to_1600x900() -> None:
    output, _meta = normalize_editorial_image_bytes(_make_image_bytes(1536, 1024))
    with Image.open(io.BytesIO(output)) as img:
        assert img.size == (TARGET_WIDTH, TARGET_HEIGHT)


def test_normalize_portrait_to_1600x900() -> None:
    output, _meta = normalize_editorial_image_bytes(_make_image_bytes(900, 1600))
    with Image.open(io.BytesIO(output)) as img:
        assert img.size == (TARGET_WIDTH, TARGET_HEIGHT)


def test_output_is_jpeg() -> None:
    output, meta = normalize_editorial_image_bytes(_make_image_bytes(1792, 1024))
    assert output[:2] == b"\xff\xd8"
    assert meta["mime_type"] == "image/jpeg"
    assert meta["provider_size"] == "1536x1024"
    assert meta["final_size"] == "1600x900"


def test_provider_size_1536x1024_crops_to_1600x900_without_stretch() -> None:
    """1536x1024 (3:2) → vertical center crop to 16:9 → 1600x900."""
    output, meta = normalize_editorial_image_bytes(_make_image_bytes(1536, 1024))
    with Image.open(io.BytesIO(output)) as img:
        assert img.size == (TARGET_WIDTH, TARGET_HEIGHT)
        ratio = img.size[0] / img.size[1]
        assert abs(ratio - (16 / 9)) < 0.001
    assert meta["width"] == 1600
    assert meta["height"] == 900
