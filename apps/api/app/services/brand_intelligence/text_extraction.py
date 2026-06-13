"""Extract plain text from uploaded brand source documents."""

from __future__ import annotations

import io
from typing import Final

ALLOWED_CONTENT_TYPES: Final[frozenset[str]] = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown",
    }
)

ALLOWED_EXTENSIONS: Final[frozenset[str]] = frozenset({".pdf", ".docx", ".txt", ".md"})

MAX_FILE_BYTES: Final[int] = 15 * 1024 * 1024
MAX_BATCH_FILES: Final[int] = 10


class TextExtractionError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def normalize_content_type(content_type: str | None, filename: str) -> str:
    if content_type and content_type.split(";")[0].strip().lower() in ALLOWED_CONTENT_TYPES:
        return content_type.split(";")[0].strip().lower()
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if lower.endswith(".md"):
        return "text/markdown"
    if lower.endswith(".txt"):
        return "text/plain"
    raise TextExtractionError(f"Tipo file non supportato: {filename}")


def validate_file_size(size: int, filename: str) -> None:
    if size <= 0:
        raise TextExtractionError(f"File vuoto: {filename}")
    if size > MAX_FILE_BYTES:
        raise TextExtractionError(
            f"File troppo grande ({size // (1024 * 1024)}MB). Limite: 15MB per file."
        )


def extract_text_from_bytes(*, content_type: str, filename: str, data: bytes) -> str:
    validate_file_size(len(data), filename)
    mime = normalize_content_type(content_type, filename)

    if mime == "application/pdf":
        return _extract_pdf(data, filename)
    if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx(data, filename)
    if mime in ("text/plain", "text/markdown"):
        return _extract_text(data, filename)
    raise TextExtractionError(f"Tipo file non supportato: {filename}")


def _extract_pdf(data: bytes, filename: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise TextExtractionError("Libreria pypdf non disponibile") from exc

    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text.strip())
    if not parts:
        raise TextExtractionError(
            f"Nessun testo estratto da {filename}. Il PDF potrebbe essere solo immagini."
        )
    return "\n\n".join(parts)


def _extract_docx(data: bytes, filename: str) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise TextExtractionError("Libreria python-docx non disponibile") from exc

    doc = Document(io.BytesIO(data))
    parts = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    if not parts:
        raise TextExtractionError(f"Nessun testo estratto da {filename}.")
    return "\n\n".join(parts)


def _extract_text(data: bytes, filename: str) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = data.decode(encoding).strip()
            if text:
                return text
        except UnicodeDecodeError:
            continue
    raise TextExtractionError(f"Impossibile decodificare il file di testo: {filename}")
