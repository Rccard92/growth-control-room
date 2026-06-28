"""Post-generation editorial article quality validation (non-blocking)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.services.content.editorial_safe_claims_scan import (
    EditorialSafeClaimFlag,
    scan_editorial_safe_claims,
)

if TYPE_CHECKING:
    from app.models.brand_intelligence import BrandSafeClaims
    from app.schemas.content_seo_editorial import EditorialArticlePayload, EditorialBriefPayload

_WORD_RE = re.compile(r"\b[\w']+\b", re.UNICODE)
_H2_RE = re.compile(r"<h2\b[^>]*>", re.IGNORECASE)
_H3_RE = re.compile(r"<h3\b[^>]*>", re.IGNORECASE)
_STRONG_RE = re.compile(r"<strong\b[^>]*>(.*?)</strong>", re.IGNORECASE | re.DOTALL)
_UL_OL_RE = re.compile(r"<(?:ul|ol)\b[^>]*>", re.IGNORECASE)
_P_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
_GCR_BOX_RE = re.compile(
    r'<div\s+class="(gcr-article-note|gcr-product-tip|gcr-article-cta)"',
    re.IGNORECASE,
)
_BODY_WRAPPER_RE = re.compile(r'<div\s+class="gcr-article-body"', re.IGNORECASE)
_STRIP_HTML = re.compile(r"<[^>]+>")

_LIST_REQUIRED_TYPES = frozenset(
    {
        "educational_article",
        "faq_objection_article",
        "product_guide",
    }
)

_COLD_TITLE_PATTERNS = re.compile(
    r"\b(faq\s+semplice|guida\s+completa|tutto\s+quello\s+che\s+devi\s+sapere|articolo\s+informativo)\b",
    re.IGNORECASE,
)

GCR_BOX_CLASSES = (
    "gcr-article-body",
    "gcr-article-note",
    "gcr-product-tip",
    "gcr-article-cta",
)


@dataclass(frozen=True)
class EditorialQualityMetrics:
    strong_count: int
    list_count: int
    box_count: int
    h2_count: int
    h3_count: int
    has_long_paragraphs: bool
    has_cta: bool
    has_cta_box: bool
    has_body_wrapper: bool
    html_blocks_used: tuple[str, ...]


def _strip_html(text: str) -> str:
    return _STRIP_HTML.sub(" ", text or "")


def _count_words(text: str) -> int:
    return len(_WORD_RE.findall(_strip_html(text)))


def extract_html_blocks_used(body_html: str) -> list[str]:
    found: list[str] = []
    if _BODY_WRAPPER_RE.search(body_html or ""):
        found.append("gcr-article-body")
    for match in _GCR_BOX_RE.finditer(body_html or ""):
        cls = match.group(1).lower()
        if cls not in found:
            found.append(cls)
    return found


def extract_readability_checklist(metrics: EditorialQualityMetrics) -> list[str]:
    items: list[str] = []
    if 6 <= metrics.strong_count <= 9:
        items.append(f"Grassetti strategici: {metrics.strong_count} (target 6–9)")
    elif metrics.strong_count < 6:
        items.append(f"Grassetti strategici: {metrics.strong_count} (target 6–9, pochi)")
    else:
        items.append(f"Grassetti strategici: {metrics.strong_count} (target 6–9, troppi)")
    if metrics.list_count >= 1:
        items.append("Lista puntata presente")
    else:
        items.append("Lista puntata: assente")
    if metrics.box_count >= 1:
        items.append("Box evidenza presente")
    else:
        items.append("Box evidenza: assente")
    if metrics.has_body_wrapper:
        items.append("Wrapper gcr-article-body presente")
    else:
        items.append("Wrapper gcr-article-body: assente")
    if not metrics.has_long_paragraphs:
        items.append("Paragrafi brevi")
    else:
        items.append("Paragrafi lunghi rilevati")
    if metrics.has_cta:
        items.append("CTA presente")
    else:
        items.append("CTA: assente")
    if metrics.has_cta_box:
        items.append("CTA in box visivo")
    return items


def _check_strong_usage(html: str) -> list[str]:
    warnings: list[str] = []
    strong_count = len(_STRONG_RE.findall(html))
    if strong_count < 6:
        warnings.append(
            "Pochi grassetti strategici — punta a 6–9 evidenze mirate per migliorare la scanability."
        )
    elif strong_count > 12:
        warnings.append("Troppi grassetti — riduci a 6–9 per evitare effetto 'documento evidenziato'.")
    elif strong_count > 10:
        warnings.append(
            f"Grassetti leggermente eccessivi ({strong_count}) — target consigliato 6–9."
        )

    for match in _STRONG_RE.finditer(html):
        inner = match.group(1) or ""
        if _count_words(inner) > 8:
            warnings.append("Evita grassetti su frasi troppo lunghe — max ~8 parole per strong.")
            break

    for p_match in _P_RE.finditer(html):
        para_html = p_match.group(1) or ""
        if len(re.findall(r"<strong\b", para_html, flags=re.IGNORECASE)) > 1:
            warnings.append("Massimo 1 grassetto per paragrafo — riduci le evidenze.")
            break

    return list(dict.fromkeys(warnings))


def validate_editorial_article_quality(
    body_html: str,
    payload: "EditorialArticlePayload",
    brief: "EditorialBriefPayload",
    content_type: str,
    *,
    safe_claims: "BrandSafeClaims | None" = None,
    has_verified_link_targets: bool = False,
) -> tuple[list[str], EditorialQualityMetrics, list[EditorialSafeClaimFlag]]:
    html = body_html or ""
    warnings: list[str] = []

    strong_count = len(_STRONG_RE.findall(html))
    list_count = len(_UL_OL_RE.findall(html))
    box_count = len(_GCR_BOX_RE.findall(html))
    h2_count = len(_H2_RE.findall(html))
    h3_count = len(_H3_RE.findall(html))
    html_blocks = extract_html_blocks_used(html)
    has_body_wrapper = "gcr-article-body" in html_blocks
    has_cta_box = "gcr-article-cta" in html_blocks

    has_long_paragraphs = False
    for match in _P_RE.finditer(html):
        if _count_words(match.group(1)) > 80:
            has_long_paragraphs = True
            break

    has_cta = bool(payload.cta.strip() or payload.community_cta.strip())

    warnings.extend(_check_strong_usage(html))

    if not has_body_wrapper:
        warnings.append("Manca il wrapper gcr-article-body per la typography Shopify.")

    if content_type in _LIST_REQUIRED_TYPES and list_count < 1:
        warnings.append("Manca una lista puntata utile per la scanability.")

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

    if has_cta and not has_cta_box:
        warnings.append(
            "CTA presente ma senza box gcr-article-cta — rendila più visibile in fondo all'articolo."
        )

    if not has_verified_link_targets and has_cta and not has_cta_box:
        warnings.append(
            "CTA generata senza link perché nessuna collection/prodotto verificato disponibile."
        )

    box_expected_types = frozenset({"recipe", "product_guide", "educational_article", "faq_objection_article"})
    if content_type in box_expected_types and box_count < 1:
        warnings.append(
            "Articolo leggibile ma migliorabile: pochi elementi di evidenza visiva."
        )

    if _COLD_TITLE_PATTERNS.search(payload.title or ""):
        warnings.append("Titolo potenzialmente freddo/documentale — preferisci un titolo più editoriale.")

    seo_title = (payload.seo_title or "").strip()
    meta_description = (payload.meta_description or "").strip()
    if not seo_title:
        warnings.append("SEO title assente — obbligatorio per pubblicazione Shopify completa.")
    elif len(seo_title) > 60:
        warnings.append(f"SEO title lungo ({len(seo_title)} caratteri; consigliati max 60).")
    if not meta_description:
        warnings.append(
            "Meta description assente — obbligatoria per pubblicazione Shopify completa."
        )
    elif len(meta_description) > 160:
        warnings.append(
            f"Meta description lunga ({len(meta_description)} caratteri; consigliati max 160)."
        )

    safe_flags = scan_editorial_safe_claims(
        html,
        excerpt=payload.excerpt,
        title=payload.title,
        safe_claims=safe_claims,
    )
    for flag in safe_flags:
        warnings.append(flag.to_warning())

    metrics = EditorialQualityMetrics(
        strong_count=strong_count,
        list_count=list_count,
        box_count=box_count,
        h2_count=h2_count,
        h3_count=h3_count,
        has_long_paragraphs=has_long_paragraphs,
        has_cta=has_cta,
        has_cta_box=has_cta_box,
        has_body_wrapper=has_body_wrapper,
        html_blocks_used=tuple(html_blocks),
    )
    return list(dict.fromkeys(warnings)), metrics, safe_flags
