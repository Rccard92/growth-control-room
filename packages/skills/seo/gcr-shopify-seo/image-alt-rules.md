# Image Alt Text Rules

Incorpora claude-seo `seo-images` § Alt Text, adattato per media Shopify in GCR.

## Principi (da seo-images)

- **Presente** su tutte le immagini `<img>` / media Shopify (eccetto decorative)
- **Descrittivo**: descrive il contenuto reale, non il filename
- **Naturale**: keyword dove appropriato, mai stuffing
- **Lunghezza**: 10–125 caratteri (target GCR)
- **Accessibilità**: utile a screen reader e image SEO

## Buoni esempi

- "Barattolo di miele di acacia 500g su tavolo di legno"
- "Dettaglio texture crema di miele artigianale"
- "Confezione regalo miele con fiocco e etichetta brand"

## Cattivi esempi

- "image.jpg" (filename)
- "miele miele biologico miele italiano" (keyword stuffing)
- "Clicca qui" (non descrittivo)
- "Immagine di prodotto" (generico, poco utile)

## Tipi immagine prodotto (GCR custom)

Differenziare alt per tipo di scatto:

| Tipo | Alt deve descrivere |
|------|---------------------|
| Prodotto | Prodotto principale, formato, colore visibile |
| Packaging | Confezione, etichetta, formato vendita |
| Dettaglio | Texture, ingrediente, particolare qualità |
| Lifestyle | Contesto d'uso senza claim inventati |

## Scoring (prodotti)

- **100**: tutte le immagini media hanno alt non vuoto (10–125 char ideale)
- **50**: featured ha alt, altre mancanti o generiche
- **0**: nessun alt su immagini disponibili
- **N/A (100)**: nessuna immagine in payload → skip issue

## Scoring (collections)

- **100**: `image_alt` presente e descrittivo
- **50**: alt generico (< 10 char o "image")
- **0**: assente

## Proposta AI

Per prodotti, array in `media_images`:

```json
{ "id": "...", "alt": "...", "proposed_alt": "..." }
```

Solo per immagini reali sincronizzate. Non inventare contenuto visivo non deducibile dal prodotto.

## Vincoli proposta

- Non inventare colori, materiali o contesti non supportati da title/description/tags
- Non ripetere verbatim il product title in ogni alt
- Ogni immagine deve avere alt **distinto** se mostra angolazioni/contesti diversi
