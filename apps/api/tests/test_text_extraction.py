"""Text extraction unit tests."""

import pytest

from app.services.brand_intelligence.text_extraction import (
    TextExtractionError,
    extract_text_from_bytes,
    validate_file_size,
)


def test_extract_plain_text() -> None:
    data = b"Ciao mondo\nSeconda riga"
    text = extract_text_from_bytes(content_type="text/plain", filename="note.txt", data=data)
    assert "Ciao mondo" in text


def test_extract_markdown() -> None:
    data = b"# Brand\n\nDescrizione breve"
    text = extract_text_from_bytes(content_type="text/markdown", filename="brand.md", data=data)
    assert "Brand" in text


def test_unsupported_file_type() -> None:
    with pytest.raises(TextExtractionError, match="non supportato"):
        extract_text_from_bytes(content_type="image/png", filename="logo.png", data=b"fake")


def test_file_too_large() -> None:
    with pytest.raises(TextExtractionError, match="15MB"):
        validate_file_size(16 * 1024 * 1024, "big.pdf")
