"""Regression tests for the editorial article HTML sanitizer."""

from app.utils.html_sanitize import (
    sanitize_editorial_article_html,
    sanitize_editorial_article_html_with_warnings,
)

ARTICLE_BODY = "gcr-article-body"


def test_disallowed_div_does_not_close_the_outer_wrapper() -> None:
    """A div with an unknown class must not truncate the article wrapper."""
    html = (
        f'<div class="{ARTICLE_BODY}">'
        "<p>Intro.</p>"
        '<div class="faq"><h3>Domanda?</h3><p>Risposta.</p></div>'
        "<h2>Conclusione</h2><p>Finale.</p>"
        "</div>"
    )
    result = sanitize_editorial_article_html_with_warnings(html)

    assert result.html == (
        f'<div class="{ARTICLE_BODY}">'
        "<p>Intro.</p><h3>Domanda?</h3><p>Risposta.</p>"
        "<h2>Conclusione</h2><p>Finale.</p>"
        "</div>"
    )
    assert any("faq" in w for w in result.warnings)


def test_compliant_article_is_left_untouched() -> None:
    html = (
        f'<div class="{ARTICLE_BODY}">'
        "<p>Intro.</p><h2>Sezione</h2><p>Testo.</p>"
        '<div class="gcr-article-note"><strong>Da ricordare:</strong> nota.</div>'
        '<div class="gcr-article-cta"><strong>CTA</strong><p>desc</p>'
        '<a href="/collections/miele">Scopri</a></div>'
        "</div>"
    )
    assert sanitize_editorial_article_html(html) == html


def test_tables_survive_sanitization() -> None:
    html = (
        '<table><thead><tr><th scope="col">Ingrediente</th><th>Quantita</th></tr></thead>'
        '<tbody><tr><td>Farina</td><td colspan="2">200g</td></tr></tbody></table>'
    )
    assert sanitize_editorial_article_html(html) == html


def test_line_breaks_and_images_survive() -> None:
    html = '<p>Riga uno<br>Riga due</p><p><img src="https://cdn.shopify.com/x.jpg" alt="foto"></p>'
    out = sanitize_editorial_article_html(html)
    assert "<br>" in out
    assert '<img src="https://cdn.shopify.com/x.jpg" alt="foto" loading="lazy">' in out


def test_void_tags_never_emit_a_closing_tag() -> None:
    out = sanitize_editorial_article_html("<p>a<br/>b</p>")
    assert "</br>" not in out
    assert out == "<p>a<br>b</p>"


def test_unsafe_image_source_is_dropped() -> None:
    out = sanitize_editorial_article_html('<p><img src="javascript:alert(1)" alt="x"></p>')
    assert "javascript" not in out
    assert "<img" not in out


def test_script_and_style_content_is_removed() -> None:
    out = sanitize_editorial_article_html('<p>a</p><script>var x="boom";</script><p>b</p>')
    assert out == "<p>a</p><p>b</p>"
    out = sanitize_editorial_article_html("<style>body{display:none}</style><p>b</p>")
    assert out == "<p>b</p>"


def test_event_handlers_are_stripped() -> None:
    assert sanitize_editorial_article_html('<p onclick="alert(1)">t</p>') == "<p>t</p>"


def test_anchor_without_safe_href_keeps_text_and_drops_tag() -> None:
    out = sanitize_editorial_article_html('<a href="javascript:alert(1)">bad</a>')
    assert out == "bad"


def test_target_blank_gets_noopener() -> None:
    out = sanitize_editorial_article_html('<a href="https://x.it" target="_blank">l</a>')
    assert 'target="_blank"' in out
    assert "noopener" in out and "noreferrer" in out


def test_headings_are_remapped_instead_of_flattened() -> None:
    assert sanitize_editorial_article_html("<h1>Titolo</h1>") == "<h2>Titolo</h2>"
    assert sanitize_editorial_article_html("<h5>Piccolo</h5>") == "<h4>Piccolo</h4>"
    assert sanitize_editorial_article_html("<p><b>x</b><i>y</i></p>") == (
        "<p><strong>x</strong><em>y</em></p>"
    )


def test_escaped_markup_stays_text() -> None:
    out = sanitize_editorial_article_html("<p>usa &lt;script&gt; nel codice</p>")
    assert out == "<p>usa &lt;script&gt; nel codice</p>"


def test_orphan_closing_tags_are_ignored() -> None:
    assert sanitize_editorial_article_html("<p>a</p></div></ul><p>b</p>") == "<p>a</p><p>b</p>"


def test_empty_input() -> None:
    assert sanitize_editorial_article_html("") == ""
    assert sanitize_editorial_article_html("   ") == ""
