# Regole Internal Linking

## Pattern URL Shopify

- Prodotti: `/products/{handle}` o URL assoluto shop + `/products/{handle}`
- Collections: `/collections/{handle}`

## Rilevamento (audit)

Scansionare `body_html` / `body_text` degli articoli per:

- href contenenti `/products/`
- href contenenti `/collections/`
- menzione handle prodotto in anchor text (fallback debole)

## Suggerimenti (opportunity)

1. **Articolo → prodotto best seller** — link al prodotto più venduto correlato (stesso product_type o tag)
2. **Articolo → collection** — link alla collection pillar del topic
3. **Collection description → articoli** — link ad articoli guida esistenti (futuro)
4. **Prodotto → articolo guida** — quando esiste blog_topic opportunity

## Anchor text

- Usare title prodotto/collection reale
- Evitare "clicca qui"
- Preferire keyword da handle/title esistente

## Limiti

- Non suggerire link a entità non sincronizzate
- Non inventare URL o handle
