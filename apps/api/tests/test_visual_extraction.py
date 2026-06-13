"""Visual extraction unit tests (HTML fixtures, no HTTP)."""

from app.services.brand_intelligence.visual_extraction import (
    _assign_roles,
    _extract_colors_from_css,
    _extract_fonts_from_css,
    _normalize_hex,
    _VisualHTMLParser,
)


SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta property="og:image" content="https://example.com/logo.png" />
  <link rel="icon" href="/favicon.ico" />
  <style>
    body { color: #111111; background: #FFFFFF; font-family: "Inter", sans-serif; }
    .accent { color: rgb(255, 128, 0); }
  </style>
</head>
<body style="background:#FAFAFA">
  <header>
    <img src="/header-logo.svg" alt="Logo" />
  </header>
</body>
</html>
"""


def test_normalize_hex_short_form() -> None:
    assert _normalize_hex("#abc") == "#AABBCC"


def test_extract_colors_from_css() -> None:
    colors = _extract_colors_from_css(
        "body { color: #111111; background: #FFFFFF; } .x { color: rgb(255, 128, 0); }"
    )
    hexes = [c[0] for c in colors]
    assert "#111111" in hexes
    assert "#FFFFFF" in hexes
    assert "#FF8000" in hexes


def test_assign_roles_assigns_primary() -> None:
    swatches = _assign_roles([("#336699", 5), ("#FFFFFF", 3), ("#111111", 2)])
    assert swatches[0].role == "primary"
    assert swatches[0].hex == "#336699"


def test_extract_fonts_from_css() -> None:
    fonts = _extract_fonts_from_css('body { font-family: "Inter", sans-serif; }')
    assert len(fonts) >= 1
    assert fonts[0].name == "Inter"


def test_visual_html_parser_og_image_and_favicon() -> None:
    parser = _VisualHTMLParser("https://example.com")
    parser.feed(SAMPLE_HTML)
    parser.close()
    assert parser.og_image == "https://example.com/logo.png"
    assert parser.favicon == "https://example.com/favicon.ico"
    assert len(parser.header_images) >= 1
