# Product SEO Rules (Shopify)

Adattato da claude-seo `seo-ecommerce` § Product Page Analysis per i campi Shopify sincronizzati in GCR.

## Campi Shopify analizzati

| Campo | Fonte | Ruolo SEO |
|-------|-------|-----------|
| `title` | Product title | Nome commerciale in scheda (H1 equivalente) |
| `handle` | URL slug | Leggibilità, keyword nel path |
| `seo_title` | metafields global title_tag | Title tag SERP (distinto da product title) |
| `seo_description` | metafields global description_tag | Meta description SERP |
| `descriptionHtml` / `description_text` | body prodotto | Contenuto, keyword naturali, conversione |
| `tags` | tags array | Categorizzazione, long-tail |
| `productType` | product_type | Contesto semantico |
| `vendor` | vendor | Brand name in SEO title |
| `media_images[].alt` | media alt text | Image SEO + accessibilità |
| stock / inventory | varianti | Priorità business (no copy inventato) |
| vendite | `ShopifyOrderLineItem` | Boost severity best-seller |

## Componenti score (pesi GCR)

| Componente | Peso | Ottimo | Warning | Critico |
|------------|------|--------|---------|---------|
| score_title | 15 | Titolo chiaro ≥ 10 char | < 10 char | Assente |
| score_seo_title | 20 | Presente 30–60 char | < 30 o > 70 | Assente |
| score_meta_description | 20 | Presente 120–160 char | < 120 o > 170 | Assente |
| score_description | 15 | body ≥ 150 char testo | 50–149 | < 50 o assente |
| score_handle | 10 | handle leggibile kebab-case | corto/generico | assente |
| score_image_alt | 10 | tutte immagini con alt | parziale | nessun alt |
| score_tags | 10 | 1–10 tag coerenti | 0 tag | tag incoerenti |

Implementazione runtime: `seo_scoring_engine.py` + `seo_scoring_constants.py`.

## Regole title (product title)

- [ ] Chiaro e descrittivo, minimo 10 caratteri
- [ ] Nome prodotto riconoscibile senza keyword stuffing
- [ ] Coerente con `productType` e `vendor`
- [ ] Distinto da `seo_title` (product title = scheda; SEO title = SERP)

## Regole SEO title

- [ ] Presente (non lasciare vuoto se possibile)
- [ ] 30–60 caratteri (ottimale per SERP)
- [ ] Formato consigliato: `[Product Name] - [Key Feature] | [Brand]`
- [ ] Include brand (`vendor`) dove naturale
- [ ] Non duplicare verbatim il product title se aggiunge poco valore

## Regole meta description

- [ ] Presente
- [ ] 120–160 caratteri
- [ ] Contiene beneficio reale dal prodotto (da description/tags)
- [ ] Call-to-action naturale (es. scopri, acquista) senza claim inventati
- [ ] Non ripetere solo il title

## Regole description (body)

- [ ] Testo plain ≥ 150 caratteri (da `description_text`)
- [ ] Struttura leggibile (paragrafi, elenchi in HTML)
- [ ] Features/benefici verificabili dai dati esistenti
- [ ] H2 consigliati in futuro: Features, Specifications (non obbligatorio in v1)

## Regole handle

- [ ] Kebab-case leggibile (`miele-acacia-500g`)
- [ ] Minimo 3 caratteri
- [ ] Evitare handle generici (`product-1`, `item`)
- [ ] Coerente con keyword principale senza stuffing

## Regole tags

- [ ] 1–10 tag coerenti con prodotto
- [ ] Derivati da title, productType, vendor reali
- [ ] No tag duplicati o irrilevanti

## Priorità business

Boost severity se:

- Best seller (top vendite) con score < 60 → minimo warning
- Stock > 0, zero vendite, score < 50 → opportunity alta

## Futuro (non implementato in v1)

- Internal linking: breadcrumb Home > Collection > Product
- Related products cross-sell
- Product JSON-LD schema (vedi `schema-rules.md`)

## Issues JSON structure

```json
{ "code": "missing_seo_title", "severity": "critical", "message": "...", "field": "seo_title" }
```
