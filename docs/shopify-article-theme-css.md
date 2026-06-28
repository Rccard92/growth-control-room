# CSS tema Shopify per articoli GCR

Aggiungi questo CSS al tema Shopify (es. `assets/gcr-article.css` + include nel layout blog) per rendere visibili i box generati dagli articoli editoriali GCR.

GCR **non inietta** automaticamente questo CSS nel tema — va applicato manualmente una volta.

## Classi supportate

| Classe | Uso |
|--------|-----|
| `.gcr-article-note` | Box "Da ricordare" |
| `.gcr-product-tip` | Box "Consiglio Solmielato" |
| `.gcr-article-cta` | CTA visiva con link prodotto |

## CSS consigliato

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
}

.gcr-article-note strong,
.gcr-product-tip strong,
.gcr-article-cta strong {
  display: inline;
  font-weight: 600;
}

.gcr-article-cta a {
  color: inherit;
  text-decoration: underline;
}
```

## Note

- Gli articoli GCR usano solo tag HTML whitelist: `h2`, `h3`, `p`, `ul`, `ol`, `li`, `strong`, `em`, `a`, `blockquote`, `div` con classi sopra.
- Nessuno style inline viene generato — il tema deve fornire lo stile.
- Safe Claims e sanitizzazione backend rimangono attivi indipendentemente dal CSS tema.
