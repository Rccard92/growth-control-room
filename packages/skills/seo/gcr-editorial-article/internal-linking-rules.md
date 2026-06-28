# Regole internal linking

## Obiettivo

Inserire **1–3 link interni reali** a prodotti e collezioni Shopify verificati — senza inventare URL.

## Blocco LINK INTERNI VERIFICATI

Il prompt include un array JSON con target verificati dal database:

```json
[
  {"type": "product", "title": "Miele millefiori", "handle": "miele-millefiori", "path": "/products/miele-millefiori"},
  {"type": "collection", "title": "Mieli biologici", "handle": "mieli-bio", "path": "/collections/mieli-bio"}
]
```

Usa **solo** questi path per `<a href="...">` nel bodyHtml.

## Quando linkare nel bodyHtml

- Max **1–3** link totali nell'articolo
- Path da blocco verificato: `/products/{handle}` o `/collections/{handle}`
- Anchor text naturale (titolo prodotto/collezione o variante breve)

## Quando NON linkare

- Target non presenti nel blocco verificato → **non inventare** URL
- Salva suggerimenti in `internalLinkSuggestions` (testo descrittivo)
- Popola `linkedProducts` / `linkedCollections` con titoli verificati anche se non linkati nel testo

## Brief: internalLinkingPlan

- Elenca prodotti/collezioni da collegare con path se handle noto
- Se handle sconosciuto: "Suggerire collezione X (handle da verificare in sync Shopify)"

## Articolo: payload

- `linkedProducts`: titoli prodotti verificati usati o suggeriti
- `linkedCollections`: titoli collezioni verificate
- `internalLinkSuggestions`: voci testuali per link futuri senza URL

## Priorità link

1. Prodotto collegato all'item editoriale (handle item)
2. Prodotti in `productsToLink` del brief (match DB)
3. Collezioni pertinenti alla keyword (match DB, max 2–3)
4. Mai articoli correlati senza URL reale
