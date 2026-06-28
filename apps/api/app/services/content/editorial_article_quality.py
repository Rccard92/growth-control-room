"""Post-generation editorial article quality validation (non-blocking)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.content_seo_editorial import EditorialArticlePayload, EditorialBriefPayload

_WORD_RE = re.compile(r"\b[\w']+\b", re.UNICODE)
_H2_RE = re.compile(r"<h2\b[^>]*>", re.IGNORECASE)
_H3_RE = re.compile(r"<h3\b[^>]*>", re.IGNORECASE)
_STRONG_RE = re.compile(r"<strong\b[^>]*>", re.IGNORECASE)
_UL_OL_RE = re.compile(r"<(?:ul|ol)\b[^>]*>", re.IGNORECASE)
_P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_GCR_BOX_RE = re.compile(
    r'<div\s+class="(gcr-article-note|gcr-product-tip|gcr-article-cta)"',
    re.IGNORECASE,
)
_STRIP_HTML = re.compile(r"<[^>]+>")

_LIST_REQUIRED_TYPES = frozenset(
    {
        "educational_article",
        "faq_objection_article",
        "product_guide",
    }
)

_MEDICAL_PATTERN = re.compile(
    r"\b(cura|guarisce|guarigione|terapeutico|medicinale|previene\s+(?:la|il|le|i)\s+\w+|"
    r"antibiotico\s+naturale|effetto\s+curativo)\b",
    re.IGNORECASE,
)

GCR_BOX_CLASSES = ("gcr-article-note", "gcr-product-tip", "gcr-article-cta")


@dataclass(frozen=True)
class EditorialQualityMetrics:
    strong_count: int
    list_count: int
    box_count: int
    h2_count: int
    h3_count: int
    has_long_paragraphs: bool
    has_cta: bool
    html_blocks_used: tuple[str, ...]


def _strip_html(text: str) -> str:
    return _STRIP_HTML.sub(" ", text or "")


def _count_words(text: str) -> int:
    return len(_WORD_RE.findall(_strip_html(text)))


def extract_html_blocks_used(body_html: str) -> list[str]:
    found: list[str] = []
    for match in _GCR_BOX_RE.finditer(body_html or ""):
        cls = match.group(1).lower()
        if cls not in found:
            found.append(cls)
    return found


def extract_readability_checklist(metrics: EditorialQualityMetrics) -> list[str]:
    items: list[str] = []
    if metrics.strong_count >= 4:
        items.append(f"Grassetti strategici: {metrics.strong_count}")
    else:
        items.append("Grassetti strategici: insufficienti")
    if metrics.list_count >= 1:
        items.append("Lista puntata presente")
    else:
        items.append("Lista puntata: assente")
    if metrics.box_count >= 1:
        items.append("Box evidenza presente")
    else:
        items.append("Box evidenza: assente")
    if not metrics.has_long_paragraphs:
        items.append("Paragrafi brevi")
    else:
        items.append("Paragrafi lunghi rilevati")
    if metrics.has_cta:
        items.append("CTA presente")
    else:
        items.append("CTA: assente")
    return items


def validate_editorial_article_quality(
    body_html: str,
    payload: "EditorialArticlePayload",
    brief: "EditorialBriefPayload",
    content_type: str,
) -> tuple[list[str], EditorialQualityMetrics]:
    html = body_html or ""
    warnings: list[str] = []

    strong_count = len(_STRONG_RE.findall(html))
    list_count = len(_UL_OL_RE.findall(html))
    box_count = len(_GCR_BOX_RE.findall(html))
    h2_count = len(_H2_RE.findall(html))
    h3_count = len(_H3_RE.findall(html))
    html_blocks = extract_html_blocks_used(html)

    has_long_paragraphs = False
    for match in _P_RE.finditer(html):
        if _count_words(match.group(1)) > 80:
            has_long_paragraphs = True
            break

    has_cta = bool(payload.cta.strip() or payload.community_cta.strip())

    if content_type in _LIST_REQUIRED_TYPES and list_count < 1:
        warnings.append("Manca una lista puntata utile per la scanability.")

    if strong_count < 4:
        warnings.append("Pochi grassetti strategici — l'articolo potrebbe risultare piatto.")
    elif strong_count > 12:
        warnings.append("Troppi grassetti — riduci l'evidenza visiva.")

    if has_long_paragraphs:
        warnings.append("Paragrafi troppo lunghi — spezza il testo per migliorare la leggibilità.")

    max_h2 = brief.max_h2 if brief.max_h2 is not None else 5
    if h2_count > max_h2:
        warnings.append(f"Articolo con {h2_count} H2 (max consigliato {max_h2}).")

    max_faq = 3 if (brief.structure_complexity or "") != "approfondita" else 4
    text_lower = _strip_html(html).lower()
    if any(m in text_lower for m in ("domande frequenti", "faq")) and h3_count > max_faq:
        warnings.append(f"Sezione FAQ ampia ({h3_count} elementi) — verifica compattezza.")

    if not has_cta:
        warnings.append("CTA finale assente — aggiungi invito commerciale o community.")

    box_expected_types = frozenset({"recipe", "product_guide", "educational_article", "faq_objection_article"})
    if content_type in box_expected_types and box_count < 1:
        warnings.append(
            "Articolo leggibile ma migliorabile: pochi elementi di evidenza visiva."
        )

    plain = _strip_html(html)
    if _MEDICAL_PATTERN.search(plain):
        warnings.append(
            "Verifica Safe Claims: possibile linguaggio medico/terapeutico nel testo."
        )

    metrics = EditorialQualityMetrics(
        strong_count=strong_count,
        list_count=list_count,
        box_count=box_count,
        h2_count=h2_count,
        h3_count=h3_count,
        has_long_paragraphs=has_long_paragraphs,
        has_cta=has_cta,
        html_blocks_used=tuple(html_blocks),
    )
    return list(dict.fromkeys(warnings)), metrics
