"""Tests for editorial Safe Claims scan."""

from types import SimpleNamespace

from app.services.content.editorial_safe_claims_scan import scan_editorial_safe_claims


def test_scan_forbidden_claim_returns_phrase() -> None:
    safe_claims = SimpleNamespace(
        forbidden_claims=["cura delle malattie"],
        caution_claims=[],
        health_claim_rules=[],
        tone_red_flags=[],
    )
    html = "<p>Questo miele aiuta la cura delle malattie in modo naturale.</p>"
    flags = scan_editorial_safe_claims(html, safe_claims=safe_claims)
    assert len(flags) >= 1
    assert flags[0].severity == "high"
    assert "cura" in flags[0].phrase.lower() or "malattie" in flags[0].phrase.lower()
    assert "Possibile claim" in flags[0].to_warning()


def test_scan_generic_health_pattern() -> None:
    html = "<p>Il miele aiuta il benessere quotidiano della famiglia.</p>"
    flags = scan_editorial_safe_claims(html)
    assert any("benessere" in f.phrase.lower() for f in flags)
    assert flags[0].severity == "medium"
    assert flags[0].suggestion
