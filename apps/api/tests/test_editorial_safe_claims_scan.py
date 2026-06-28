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


def test_scan_lavorato_con_cura_no_flag() -> None:
    html = (
        "<p>Può capitare anche con un miele biologico artigianale, "
        "lavorato con cura e nel rispetto del prodotto naturale.</p>"
    )
    flags = scan_editorial_safe_claims(html)
    assert len(flags) == 0


def test_scan_a_cura_di_no_flag() -> None:
    flags = scan_editorial_safe_claims("", title="A cura di Davide")
    assert len(flags) == 0


def test_scan_generic_health_pattern() -> None:
    html = "<p>Il miele aiuta il benessere quotidiano della famiglia.</p>"
    flags = scan_editorial_safe_claims(html)
    assert any("benessere" in f.phrase.lower() for f in flags)
    assert flags[0].severity == "medium"


def test_scan_sistema_immunitario() -> None:
    html = "<p>Il miele aiuta il sistema immunitario.</p>"
    flags = scan_editorial_safe_claims(html)
    assert len(flags) >= 1
    assert any("immunitario" in f.phrase.lower() for f in flags)
