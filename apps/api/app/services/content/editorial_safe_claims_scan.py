"""Scan editorial article text for Safe Claims violations with precise phrase feedback."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.models.brand_intelligence import BrandSafeClaims

Severity = Literal["low", "medium", "high"]

_STRIP_HTML = re.compile(r"<[^>]+>")
_ARTISAN_CURA_RE = re.compile(
    r"\b(?:lavorato|fatto|selezionato|preparato|realizzato)\s+con\s+cura\b|"
    r"\ba\s+cura\s+di\b|"
    r"\b(?:con|a)\s+cura\b|"
    r"\bcura\s+artigianale\b|"
    r"\battenzione\s+alla\s+qualit[aà]\b",
    re.IGNORECASE,
)

_GENERIC_HEALTH_PATTERNS: list[tuple[str, str, str]] = [
    (
        r"\b(cura\s+(?:delle|dei|degli|del|di\s+la|di)\s+\w+|guarisce|guarigione|terapeutico|medicinale|curativo)\b",
        "potenziale linguaggio medico/terapeutico",
        "sostituire con formulazione descrittiva non terapeutica",
    ),
    (
        r"\b(preven(e|gono|zione)\s+(?:la|il|le|i)\s+\w+|aiuta\s+a\s+prevenire)\b",
        "potenziale claim preventivo non verificabile",
        "evitare promesse di prevenzione; descrivere uso e caratteristiche",
    ),
    (
        r"\b(benessere\s+quotidiano|aiuta\s+il\s+benessere|fa\s+bene\s+alla\s+salute|sistema\s+immunitario)\b",
        "potenziale claim salutistico generico",
        "sostituire con 'si inserisce con semplicità nella routine quotidiana'",
    ),
    (
        r"\b(antibiotico\s+naturale|effetto\s+curativo|antinfiammatorio|antibatterico|depurativo|rimedio\s+naturale)\b",
        "claim salutistico non consentito",
        "rimuovere riferimenti a proprietà curative",
    ),
]


@dataclass(frozen=True)
class EditorialSafeClaimFlag:
    severity: Severity
    phrase: str
    reason: str
    suggestion: str

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "phrase": self.phrase,
            "reason": self.reason,
            "suggestion": self.suggestion,
        }

    def to_warning(self) -> str:
        return f"Possibile claim da verificare: «{self.phrase}» — {self.reason}"


def _strip_html(html: str) -> str:
    return _STRIP_HTML.sub(" ", html or "")


def _is_artisan_cura_context(sentence: str, matched: str) -> bool:
    if _ARTISAN_CURA_RE.search(sentence):
        return True
    if matched.lower() == "cura" and re.search(r"(?:con|a)\s+cura\b", sentence, re.IGNORECASE):
        return True
    return False


def _extract_sentence(text: str, match_start: int) -> str:
    text = text.strip()
    if not text:
        return ""
    before = text[:match_start]
    after = text[match_start:]
    start = max(before.rfind("."), before.rfind("!"), before.rfind("?")) + 1
    end_candidates = [after.find(c) for c in ".!?" if after.find(c) >= 0]
    end_rel = min(end_candidates) if end_candidates else len(after)
    if end_rel == len(after):
        sentence = text[start : match_start + len(after)].strip()
    else:
        sentence = text[start : match_start + end_rel + 1].strip()
    return sentence[:200] if sentence else text[max(0, match_start - 40) : match_start + 80].strip()


def _scan_rule_list(
    plain: str,
    rules: list[str] | None,
    *,
    severity: Severity,
    reason_prefix: str,
    suggestion: str,
    seen_phrases: set[str],
    flags: list[EditorialSafeClaimFlag],
) -> None:
    if not rules:
        return
    lower_plain = plain.lower()
    for rule in rules:
        rule_text = str(rule).strip()
        if not rule_text or len(rule_text) < 4:
            continue
        idx = lower_plain.find(rule_text.lower())
        if idx < 0:
            continue
        phrase = _extract_sentence(plain, idx)
        if not phrase or phrase.lower() in seen_phrases:
            continue
        if _is_artisan_cura_context(phrase, rule_text):
            continue
        seen_phrases.add(phrase.lower())
        flags.append(
            EditorialSafeClaimFlag(
                severity=severity,
                phrase=phrase,
                reason=f"{reason_prefix}: «{rule_text[:80]}»",
                suggestion=suggestion,
            )
        )


def scan_editorial_safe_claims(
    body_html: str,
    excerpt: str = "",
    title: str = "",
    *,
    safe_claims: BrandSafeClaims | None = None,
) -> list[EditorialSafeClaimFlag]:
    """Return structured Safe Claims flags with exact phrase, severity and suggestion."""
    plain = " ".join(
        part.strip()
        for part in (_strip_html(body_html), excerpt, title)
        if part and part.strip()
    )
    if not plain:
        return []

    flags: list[EditorialSafeClaimFlag] = []
    seen_phrases: set[str] = set()

    if safe_claims is not None:
        _scan_rule_list(
            plain,
            safe_claims.forbidden_claims,
            severity="high",
            reason_prefix="claim vietato da Safe Claims",
            suggestion="rimuovere o riformulare secondo Safe Claims del brand",
            seen_phrases=seen_phrases,
            flags=flags,
        )
        _scan_rule_list(
            plain,
            safe_claims.caution_claims,
            severity="medium",
            reason_prefix="claim in cautela da Safe Claims",
            suggestion="verificare con Safe Claims e preferire formulazione più prudente",
            seen_phrases=seen_phrases,
            flags=flags,
        )
        _scan_rule_list(
            plain,
            safe_claims.health_claim_rules,
            severity="medium",
            reason_prefix="regola health claim",
            suggestion="evitare claim salutistici; descrivere caratteristiche oggettive del prodotto",
            seen_phrases=seen_phrases,
            flags=flags,
        )
        _scan_rule_list(
            plain,
            safe_claims.tone_red_flags,
            severity="low",
            reason_prefix="red flag tono brand",
            suggestion="allineare il tono alle Editorial Guidelines",
            seen_phrases=seen_phrases,
            flags=flags,
        )

    for pattern, reason, suggestion in _GENERIC_HEALTH_PATTERNS:
        for match in re.finditer(pattern, plain, flags=re.IGNORECASE):
            matched = match.group(0)
            phrase = _extract_sentence(plain, match.start())
            if not phrase or phrase.lower() in seen_phrases:
                continue
            if _is_artisan_cura_context(phrase, matched):
                continue
            seen_phrases.add(phrase.lower())
            flags.append(
                EditorialSafeClaimFlag(
                    severity="medium",
                    phrase=phrase,
                    reason=reason,
                    suggestion=suggestion,
                )
            )

    return flags
