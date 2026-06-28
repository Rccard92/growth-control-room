"""Light post-processing for editorial article HTML (anti-repetition, structure checks)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.content_seo_editorial import EditorialBriefPayload

_WORD_RE = re.compile(r"\b[\w']+\b", re.UNICODE)
_H2_RE = re.compile(r"<h2\b[^>]*>.*?</h2>", re.IGNORECASE | re.DOTALL)
_H3_RE = re.compile(r"<h3\b[^>]*>.*?</h3>", re.IGNORECASE | re.DOTALL)
_FIRST_P_RE = re.compile(r"(<p\b[^>]*>)(.*?)(</p>)", re.IGNORECASE | re.DOTALL)


def _tokenize(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text) if len(w) > 2}


def _word_overlap_ratio(a: str, b: str) -> float:
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    return len(intersection) / min(len(tokens_a), len(tokens_b))


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "")


def _remove_duplicate_intro(body_html: str, excerpt: str) -> tuple[str, bool]:
    if not body_html.strip() or not excerpt.strip():
        return body_html, False
    match = _FIRST_P_RE.search(body_html)
    if not match:
        return body_html, False
    first_para_text = _strip_html(match.group(2))
    if _word_overlap_ratio(first_para_text, excerpt) >= 0.7:
        return body_html[: match.start()] + body_html[match.end() :], True
    return body_html, False


def _count_phrase_occurrences(text: str, phrase: str) -> int:
    if not phrase.strip():
        return 0
    pattern = re.escape(phrase.strip())
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def _reduce_phrase_repetitions(text: str, phrase: str, max_occurrences: int = 2) -> tuple[str, bool]:
    if not phrase.strip():
        return text, False
    count = _count_phrase_occurrences(text, phrase)
    if count <= max_occurrences:
        return text, False
    pattern = re.compile(re.escape(phrase.strip()), flags=re.IGNORECASE)
    removed = False

    def replacer(match: re.Match[str]) -> str:
        nonlocal removed
        occurrences = getattr(replacer, "seen", 0)
        replacer.seen = occurrences + 1  # type: ignore[attr-defined]
        if replacer.seen <= max_occurrences:  # type: ignore[attr-defined]
            return match.group(0)
        removed = True
        return ""

    replacer.seen = 0  # type: ignore[attr-defined]
    cleaned = pattern.sub(replacer, text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"(<p>\s*</p>)", "", cleaned, flags=re.IGNORECASE)
    return cleaned, removed


def _count_faq_items(body_html: str) -> int:
    text = _strip_html(body_html).lower()
    faq_markers = ("faq", "domande frequenti", "domande e risposte")
    if not any(marker in text for marker in faq_markers):
        return 0
    return len(_H3_RE.findall(body_html)) or text.count("?")


def postprocess_editorial_article_html(
    body_html: str,
    excerpt: str,
    brief: "EditorialBriefPayload",
) -> tuple[str, list[str]]:
    """Apply light anti-repetition and structure validation to generated HTML."""
    warnings: list[str] = []
    html = body_html or ""

    html, intro_removed = _remove_duplicate_intro(html, excerpt)
    if intro_removed:
        warnings.append("Rimossa introduzione duplicata rispetto all'excerpt")

    for phrase in brief.avoid_repetitions or []:
        html, reduced = _reduce_phrase_repetitions(html, phrase, max_occurrences=2)
        if reduced:
            warnings.append(f"Ridotte ripetizioni eccessive: «{phrase[:60]}»")

    max_h2 = brief.max_h2
    max_h3 = brief.max_h3
    h2_count = len(_H2_RE.findall(html))
    h3_count = len(_H3_RE.findall(html))
    if max_h2 is not None and h2_count > max_h2:
        warnings.append(f"Articolo con {h2_count} H2 (max consigliato {max_h2})")
    if max_h3 is not None and h3_count > max_h3:
        warnings.append(f"Articolo con {h3_count} H3 (max consigliato {max_h3})")

    faq_count = _count_faq_items(html)
    max_faq = 4 if brief.structure_complexity != "snella" else 3
    if faq_count > max_faq:
        warnings.append(f"Sezione FAQ ampia ({faq_count} elementi) — verifica compattezza")

    return html.strip(), list(dict.fromkeys(warnings))


_BODY_WRAPPER_RE = re.compile(
    r'<div\s+class="gcr-article-body"[^>]*>',
    re.IGNORECASE,
)


def wrap_editorial_article_body(html: str) -> str:
    """Wrap article HTML in gcr-article-body if not already wrapped."""
    cleaned = (html or "").strip()
    if not cleaned:
        return '<div class="gcr-article-body"></div>'
    if _BODY_WRAPPER_RE.search(cleaned):
        return cleaned
    return f'<div class="gcr-article-body">{cleaned}</div>'
