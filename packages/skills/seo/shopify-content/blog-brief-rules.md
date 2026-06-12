# Regole Blog Brief

## Struttura ContentBrief

- `title` — working title da opportunity
- `primary_keyword` — da handle/title prodotto o collection (nullable)
- `secondary_keywords` — JSON array, max 5, solo termini derivati
- `search_intent` — informational | commercial | transactional
- `outline` — JSON: H2/H3 sections
- `internal_links` — prodotti/collections da linkare con anchor
- `products_to_feature` — prodotti reali da menzionare
- `faq` — domande da dati prodotto/collection, non inventate
- `cta` — CTA verso prodotto/collection reale

## Status brief

- `draft` — generato o manuale
- `approved` — pronto per redazione
- `exported` — esportato
- `published` — live (tracking manuale)

## In questa foundation

- Modello DB e tipi presenti
- Generazione automatica brief = step successivo
- Skill definisce solo struttura e vincoli
