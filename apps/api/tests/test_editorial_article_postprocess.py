"""Tests for editorial article body wrapper."""

from app.services.content.editorial_article_postprocess import wrap_editorial_article_body
from app.utils.html_sanitize import sanitize_editorial_article_html


def test_wrap_editorial_article_body_adds_wrapper() -> None:
    html = "<h2>Titolo</h2><p>Testo.</p>"
    wrapped = wrap_editorial_article_body(html)
    assert wrapped.startswith('<div class="gcr-article-body">')
    assert wrapped.endswith("</div>")


def test_wrap_editorial_article_body_idempotent() -> None:
    html = '<div class="gcr-article-body"><p>Già wrappato</p></div>'
    assert wrap_editorial_article_body(html) == html


def test_sanitize_preserves_gcr_article_body() -> None:
    raw = (
        '<div class="gcr-article-body">'
        '<div class="gcr-article-note"><strong>Da ricordare:</strong> test</div>'
        "</div>"
    )
    out = sanitize_editorial_article_html(raw)
    assert 'class="gcr-article-body"' in out
    assert 'class="gcr-article-note"' in out
