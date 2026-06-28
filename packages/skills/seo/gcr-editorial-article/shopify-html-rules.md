# Regole HTML Shopify per bodyHtml

## Wrapper obbligatorio

**Tutto** il contenuto articolo deve essere dentro un unico wrapper:

```html
<div class="gcr-article-body">
  <!-- h2, p, ul, box, FAQ, CTA — tutto qui dentro -->
</div>
```

Il wrapper migliora typography e spacing sul tema Shopify tramite CSS dedicato.

## Tag consentiti

`h2`, `h3`, `p`, `strong`, `em`, `ul`, `ol`, `li`, `blockquote`, `a`, `div` (solo classi GCR)

## Classi div GCR consentite

| Classe | Uso |
|--------|-----|
| `gcr-article-body` | Wrapper esterno obbligatorio |
| `gcr-article-note` | Box "Da ricordare" |
| `gcr-product-tip` | Box "Consiglio Solmielato" |
| `gcr-article-cta` | CTA finale visiva |

### Box "Da ricordare"

```html
<div class="gcr-article-note">
  <strong>Da ricordare:</strong>
  la consistenza del miele può cambiare naturalmente nel tempo.
</div>
```

### Box "Consiglio Solmielato"

```html
<div class="gcr-product-tip">
  <strong>Consiglio Solmielato:</strong>
  per valorizzare il miele millefiori, prova ad abbinarlo a formaggi freschi.
</div>
```

### CTA finale (preferita in fondo all'articolo)

Quando path collection/prodotto **verificato** disponibile nel contesto:

```html
<div class="gcr-article-cta">
  <strong>Vuoi scegliere con più calma?</strong>
  <p>Scopri le varietà di miele biologico Solmielato e confronta profumi, consistenze e usi quotidiani.</p>
  <a href="/collections/handle-verificato">Scopri la selezione</a>
</div>
```

Se **nessun** path verificato: CTA senza `<a>`, testo invito nel `<p>` — aggiungi warning in `warnings`.

## Grassetti

- Target: **6–9** `<strong>` per articolo
- Warning se `>10`; hard warning se `>12`
- Max **1 strong per paragrafo**
- Max ~8 parole dentro ogni `<strong>`
- Esempi corretti: "la cristallizzazione è naturale", "non indica da sola un difetto", "la consistenza non basta", "filiera chiara e controllata"

## Link interni

- Max **1–3** link `<a href="{path}">` nel bodyHtml
- Solo path da blocco `LINK INTERNI VERIFICATI` nel prompt (handle DB reale)
- Altrimenti: `internalLinkSuggestions` nel payload, **zero** link inventati

## Tag vietati

- `script`, `style`, `iframe`, `object`, `embed`
- Nessuno style inline
- Nessun attributo event handler

## Firma autore

- **NON** inserire firma nel bodyHtml — usa `authorName` / `authorRole`

## Tracciamento payload

- `htmlBlocksUsed`: classi usate (es. `gcr-article-body`, `gcr-article-note`, `gcr-article-cta`)
- `linkedProducts`, `linkedCollections`: titoli verificati linkati
- `skillPackUsed`: `gcr-editorial-article`
- `skillPackVersion`: es. `v1.1`
