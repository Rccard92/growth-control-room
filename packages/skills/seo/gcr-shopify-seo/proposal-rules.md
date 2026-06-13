# SEO Proposal Rules

Definisce come generare proposte SEO revisionabili per prodotti e collections Shopify.

## Vincoli universali

1. **Non inventare claim** — solo attributi da title, description, vendor, productType
2. **Non cambiare significato** — il prodotto/collection resta lo stesso articolo
3. **Output revisionabile** — ogni campo proposto è modificabile prima di approve
4. **No keyword stuffing** — keyword naturali da dati reali
5. **No modifica live** — draft → approve → apply esplicito
6. **No tag prodotto** — non generare né proporre tag in questa fase

## Product proposal JSON (runtime GCR)

Allineato a `product_current_values()` e API:

```json
{
  "product_title": "...",
  "seo_title": "...",
  "meta_description": "...",
  "handle": "...",
  "description_html": "...",
  "media_images": [{ "id": "...", "url": "...", "altText": "..." }],
  "image_alts": [
    {
      "image_id": "...",
      "current_alt": "...",
      "proposed_alt": "...",
      "reason": "..."
    }
  ],
  "reasoning": ["..."],
  "risk_level": "low|medium|high"
}
```

### Come generare ogni campo

| Campo | Regola |
|-------|--------|
| `product_title` | Migliora solo se debole/generico; mantieni nome commerciale riconoscibile |
| `seo_title` | 30–60 char; brand + keyword + beneficio breve; distinto da product_title |
| `meta_description` | 120–160 char; beneficio reale + CTA; da description esistente |
| `handle` | Kebab-case; proponi solo se generico; **high risk** se cambia URL |
| `description_html` | Arricchisci solo se < 150 char testo; non riscrivere totalmente senza necessità |
| `image_alts` | Alt descrittivo 10–125 char per ogni immagine senza alt o con alt debole |

## Collection proposal JSON (runtime GCR)

```json
{
  "collection_title": "...",
  "seo_title": "...",
  "meta_description": "...",
  "description_html": "...",
  "handle": "...",
  "image_alt": "...",
  "reasoning": ["..."],
  "risk_level": "low|medium|high"
}
```

### Come generare ogni campo

| Campo | Regola |
|-------|--------|
| `collection_title` | Chiaro, specifico per categoria |
| `seo_title` | 30–60 char; categoria + brand |
| `meta_description` | 120–160 char; gamma prodotti + CTA |
| `description_html` | Testo categoria ≥ 150 char se debole |
| `handle` | Kebab-case; high risk se cambia URL |
| `image_alt` | Descrittivo 10–125 char per hero collection |

## Risk levels

- **low**: solo meta/alt mancanti, nessun cambio title/handle
- **medium**: modifica title o description
- **high**: modifica handle o claim sensibili

## Source

- `ai`: OpenAI con regole GCR + brand guardrails
- `rules`: fallback conservativo (solo campi vuoti/deboli)
- `manual`: utente modifica nel drawer

## Workflow

1. Genera proposta (AI o rules) → UI compila direttamente il form Campi SEO
2. Utente revisiona nel drawer
3. Salva draft / approva
4. Apply su Shopify solo con scope `write_products` e conferma esplicita
