"""Tests for editorial image post-processing."""

import io

from PIL import Image

from app.services.content.editorial_image_processing import (
    EDITORIAL_IMAGE_ASPECT_RATIO,
    EDITORIAL_IMAGE_POST_PROCESSING,
    TARGET_HEIGHT,
    TARGET_WIDTH,
    normalize_editorial_image_bytes,
    read_image_dimensions,
)


def _make_image_bytes(width: int, height: int, color: str = "red") -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def test_normalize_square_to_1200x800() -> None:
    output, meta = normalize_editorial_image_bytes(_make_image_bytes(1024, 1024))
    with Image.open(io.BytesIO(output)) as img:
        assert img.size == (TARGET_WIDTH, TARGET_HEIGHT)
    assert meta["width"] == 1200
    assert meta["height"] == 800
    assert meta["aspect_ratio"] == "3:2"
    assert meta["mime_type"] == "image/jpeg"
    assert meta["post_processing_applied"] == EDITORIAL_IMAGE_POST_PROCESSING


def test_normalize_landscape_3_2_to_1200x800() -> None:
    output, _meta = normalize_editorial_image_bytes(_make_image_bytes(1536, 1024))
    with Image.open(io.BytesIO(output)) as img:
        assert img.size == (TARGET_WIDTH, TARGET_HEIGHT)
        ratio = img.size[0] / img.size[1]
        assert abs(ratio - (3 / 2)) < 0.001


def test_normalize_portrait_to_1200x800() -> None:
    output, _meta = normalize_editorial_image_bytes(_make_image_bytes(900, 1600))
    with Image.open(io.BytesIO(output)) as img:
        assert img.size == (TARGET_WIDTH, TARGET_HEIGHT)


def test_output_is_jpeg() -> None:
    output, meta = normalize_editorial_image_bytes(_make_image_bytes(1792, 1024))
    assert output[:2] == b"\xff\xd8"
    assert meta["final_size"] == "1200x800"
    assert meta["aspect_ratio"] == EDITORIAL_IMAGE_ASPECT_RATIO


def test_read_image_dimensions() -> None:
    raw = _make_image_bytes(1536, 1024)
    assert read_image_dimensions(raw) == "1536x1024"
