# Regole Content Opportunity

## Tipi (`opportunity_type`)

| Tipo | Quando | Priorità default |
|------|--------|------------------|
| blog_topic | Best seller o prodotto fermo con stock | high / medium |
| product_improvement | Meta o body prodotto debole | high se best seller, else medium |
| collection_improvement | Collection senza description/meta | medium |
| internal_linking | Articolo senza link prodotti/collections | medium |
| faq | Prodotto/collection con obiezioni comuni (issue correlata) | medium |
| comparison | Più prodotti stessa categoria/type (dati reali) | low |

## Priorità

- **high** — best seller, revenue impact, meta mancanti su prodotti top
- **medium** — stock fermo, collection deboli, internal linking
- **low** — comparison, miglioramenti marginali

## Status

- `new` — generata da analyze (rigenerabile)
- `planned` | `drafted` | `published` | `ignored` — workflow utente (non sovrascritto da analyze)

## Regole dati

- `suggested_keyword` — derivare da title/handle/product_type, mai inventare volumi
- `search_intent` — informational | commercial | transactional
- `suggested_products` / `suggested_collections` — array di `{ id, handle, title }` reali
- `reason` — spiegazione basata su metriche o issue audit
