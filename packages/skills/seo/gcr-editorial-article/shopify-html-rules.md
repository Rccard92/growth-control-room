# Regole HTML Shopify per bodyHtml

## Tag consentiti

`h2`, `h3`, `p`, `strong`, `em`, `ul`, `ol`, `li`, `blockquote`, `a`, `div` (solo con classi GCR)

## Tag vietati

- `script`, `style`, `iframe`, `object`, `embed`
- **Nessuno style inline** (`style="..."`)
- Nessun attributo event handler (`onclick`, ecc.)

## Classi div GCR consentite

### Box "Da ricordare"

```html
<div class="gcr-article-note">
  <strong>Da ricordare:</strong>
  la consistenza del miele può cambiare naturalmente nel tempo.
</div>
```

### Box "Consiglio Solmielato" (ricette / guide prodotto)

```html
<div class="gcr-product-tip">
  <strong>Consiglio Solmielato:</strong>
  per valorizzare il miele millefiori, prova ad abbinarlo a formaggi freschi.
</div>
```

### CTA visiva (opzionale)

```html
<div class="gcr-article-cta">
  <strong>Scopri la selezione:</strong>
  <a href="/products/miele-millefiori">Miele millefiori artigianale</a>
</div>
```

## Grassetti

- 5–10 frasi/parole chiave con `<strong>` (min 4, max 12)
- Mai grassetto su interi paragrafi
- Evidenziare concetti decisivi per il lettore, non keyword SEO a caso

## Link

- `<a href="/products/{handle}">` solo se handle prodotto reale fornito nel contesto
- `<a href="https://...">` solo per URL espliciti nel brief/contesto
- Altrimenti: suggerimenti in `internalLinkSuggestions`, **nessun link inventato**

## Firma autore

- **NON** inserire firma autore nel bodyHtml — usa campi `authorName` / `authorRole`

## Tracciamento payload

- `htmlBlocksUsed`: elenco classi usate (es. `gcr-article-note`, `gcr-product-tip`)
- `skillPackUsed`: `gcr-editorial-article`
- `skillPackVersion`: versione skill (es. `v1`)
