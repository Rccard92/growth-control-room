"""Post-process editorial hero images to fixed 1600x900 JPEG."""

from __future__ import annotations

import io
from typing import Any

from PIL import Image

EDITORIAL_IMAGE_FINAL_WIDTH = 1600
EDITORIAL_IMAGE_FINAL_HEIGHT = 900
EDITORIAL_IMAGE_PROVIDER_SIZE = "1536x1024"
EDITORIAL_IMAGE_FINAL_SIZE = "1600x900"
EDITORIAL_IMAGE_ASPECT_RATIO = "16:9"
JPEG_QUALITY = 90

# Backward-compatible aliases used by existing tests/imports
TARGET_WIDTH = EDITORIAL_IMAGE_FINAL_WIDTH
TARGET_HEIGHT = EDITORIAL_IMAGE_FINAL_HEIGHT
TARGET_ASPECT = EDITORIAL_IMAGE_ASPECT_RATIO


def normalize_editorial_image_bytes(raw: bytes) -> tuple[bytes, dict[str, Any]]:
    """Cover-crop and resize any input image to exactly 1600x900 JPEG."""
    with Image.open(io.BytesIO(raw)) as img:
        rgb = img.convert("RGB")
        width, height = rgb.size
        target_ratio = EDITORIAL_IMAGE_FINAL_WIDTH / EDITORIAL_IMAGE_FINAL_HEIGHT
        source_ratio = width / height

        if source_ratio > target_ratio:
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            cropped = rgb.crop((left, 0, left + new_width, height))
        else:
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            cropped = rgb.crop((0, top, width, top + new_height))

        resized = cropped.resize(
            (EDITORIAL_IMAGE_FINAL_WIDTH, EDITORIAL_IMAGE_FINAL_HEIGHT),
            Image.Resampling.LANCZOS,
        )
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        output = buffer.getvalue()

    metadata = {
        "width": EDITORIAL_IMAGE_FINAL_WIDTH,
        "height": EDITORIAL_IMAGE_FINAL_HEIGHT,
        "aspect_ratio": EDITORIAL_IMAGE_ASPECT_RATIO,
        "provider_size": EDITORIAL_IMAGE_PROVIDER_SIZE,
        "final_size": EDITORIAL_IMAGE_FINAL_SIZE,
        "mime_type": "image/jpeg",
        "extension": "jpg",
    }
    return output, metadata
