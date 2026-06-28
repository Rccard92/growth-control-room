# Regole internal linking

## Obiettivo

Suggerire link interni utili a collezioni, prodotti collegati e articoli correlati — senza inventare URL.

## Quando linkare nel bodyHtml

Inserisci `<a href="...">` nel testo **solo se**:

1. **Handle prodotto reale** disponibile nel contesto → `/products/{handle}`
2. **URL esplicito** presente in brief, Product Knowledge o internalLinksSuggestions verificati
3. Link relativi al negozio Shopify (`/collections/...`, `/products/...`) con handle noti

## Quando NON linkare

- Handle o URL non disponibili → **non inventare** link nel testo
- Prodotti menzionati genericamente senza handle → salva in `internalLinkSuggestions`
- Articoli correlati senza URL → salva suggerimento testuale in payload

## Brief: internalLinkingPlan

Compila array con voci tipo:

- "Link a prodotto collegato: /products/miele-millefiori (se handle disponibile)"
- "Suggerire collezione Mieli artigianali (handle da verificare)"
- "Articolo correlato: come conservare il miele (URL da definire)"

## Articolo: internalLinkSuggestions

Se non linkati nel body, elenca suggerimenti:

- "Collegare prodotto Miele millefiori quando handle disponibile"
- "Aggiungere link a collezione Mieli"

## Priorità link

1. Prodotto collegato all'item editoriale
2. Prodotti in `productsToLink` del brief
3. Collezioni pertinenti (solo se handle/URL noti)
4. Articoli correlati (solo se URL noti)
