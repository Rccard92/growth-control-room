# Schema Rules (Fase futura)

Adattato da claude-seo `seo-schema`. **Non implementato in v1** — reference per structured data Shopify.

## Formato preferito

- JSON-LD in `<script type="application/ld+json">`
- URL assolute (non relative)
- No placeholder text

## Tipi rilevanti per Shopify GCR

### Product

- `@type`: Product
- Required: name, image, description
- Recommended: brand, offers (price, availability), sku, gtin
- Collegare a dati reali syncati (title, media, variants)

### BreadcrumbList

- Home > Collection > Product
- Allineato a internal linking futuro

### Organization / LocalBusiness

- Brand del negozio (vendor / shop name)
- Solo dati verificabili dal merchant

## Validazione (futuro)

- Required properties per tipo
- No @context mancante
- Date e URL validi
- Evitare tipi deprecati (vedi `seo-schema/references/deprecated-types-2024-2026.md`)

## Stato GCR v1

Regole caricate come reference. Nessuna generazione o apply schema su Shopify in questa fase.
