# CSS tema Shopify per articoli GCR

Aggiungi questo CSS al tema Shopify (es. `assets/gcr-article.css` + include nel layout blog) per rendere visibili i box e la typography degli articoli editoriali GCR.

GCR **non inietta** automaticamente questo CSS nel tema — va applicato manualmente una volta.

## Classi supportate

| Classe | Uso |
|--------|-----|
| `.gcr-article-body` | Wrapper obbligatorio per typography articolo |
| `.gcr-article-note` | Box "Da ricordare" |
| `.gcr-product-tip` | Box "Consiglio Solmielato" |
| `.gcr-article-cta` | CTA finale visiva |

## Typography articolo (wrapper)

```css
.gcr-article-body {
  line-height: 1.65;
  font-size: 1rem;
  color: inherit;
}

.gcr-article-body p {
  margin: 0 0 1rem;
}

.gcr-article-body h2 {
  margin: 2rem 0 0.75rem;
  line-height: 1.3;
  font-size: 1.35rem;
}

.gcr-article-body h3 {
  margin: 1.5rem 0 0.5rem;
  line-height: 1.35;
  font-size: 1.15rem;
}

.gcr-article-body ul,
.gcr-article-body ol {
  margin: 0 0 1.25rem;
  padding-left: 1.25rem;
}

.gcr-article-body li {
  margin-bottom: 0.35rem;
}

.gcr-article-body strong {
  font-weight: 600;
}

@media (max-width: 640px) {
  .gcr-article-body {
    font-size: 0.975rem;
    line-height: 1.6;
  }

  .gcr-article-body h2 {
    font-size: 1.2rem;
  }
}
```

## Box evidenza e CTA

```css
.gcr-article-note,
.gcr-product-tip,
.gcr-article-cta {
  margin: 1.25rem 0;
  padding: 0.875rem 1rem;
  border-radius: 6px;
  font-size: 1rem;
  line-height: 1.55;
}

.gcr-article-note {
  background: #f0f9ff;
  border-left: 4px solid #0ea5e9;
}

.gcr-product-tip {
  background: #faf5ff;
  border-left: 4px solid #a855f7;
}

.gcr-article-cta {
  background: #fffbeb;
  border-left: 4px solid #f59e0b;
  padding: 1rem 1.125rem;
}

.gcr-article-note strong,
.gcr-product-tip strong,
.gcr-article-cta strong {
  display: block;
  font-weight: 600;
  margin-bottom: 0.35rem;
}

.gcr-article-cta p {
  margin: 0 0 0.75rem;
}

.gcr-article-cta a {
  color: inherit;
  font-weight: 600;
  text-decoration: underline;
}
```

## Note

- Gli articoli GCR usano solo tag HTML whitelist: `h2`, `h3`, `p`, `ul`, `ol`, `li`, `strong`, `em`, `a`, `blockquote`, `div` con classi sopra.
- Nessuno style inline viene generato — il tema deve fornire lo stile.
- Safe Claims e sanitizzazione backend rimangono attivi indipendentemente dal CSS tema.
