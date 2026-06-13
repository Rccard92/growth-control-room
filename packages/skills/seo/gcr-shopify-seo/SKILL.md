---
name: gcr-shopify-seo
version: "1.0.0"
description: >
  Growth Control Room Shopify Product & Collection SEO skill pack.
  Adapted from claude-seo (MIT) for scoring, AI proposals, and future editorial.
attribution: "Inspired by AgriciDaniel/claude-seo (seo-ecommerce, seo-images, seo-content-brief)"
---

# GCR Shopify SEO Skill

## Nome

GCR Shopify SEO Skill

## Obiettivo

Analizzare prodotti e collections Shopify con score rule-based trasparente, generare proposte SEO revisionabili (manuale/AI) e applicare modifiche solo dopo approvazione manuale.

## Input

- Prodotti sincronizzati (`ShopifyProduct`: title, handle, seo, tags, description, media, inventory, vendor, productType)
- Collections sincronizzate (`ShopifyCollection`: title, handle, description, seo, image, products_count)
- Analisi persistite (`SeoEntityAnalysis`)
- Performance vendite da `ShopifyOrderLineItem`
- Brand guardrails (tono, vincoli claim)

## Output

- Score 0–100 per componente e totale
- Issues e recommendations strutturate
- Proposte `SeoOptimizationProposal` (draft)
- Change log su apply

## Cardini fissi

1. Non inventare claim non presenti nei dati prodotto/collection
2. Non cambiare il significato del prodotto
3. Mantenere tono coerente con brand
4. Evitare keyword stuffing
5. Preferire chiarezza e conversione
6. Distinguere SEO title da titolo prodotto/collection
7. Meta description persuasiva ma realistica
8. Alt text descrittivo, 10–125 caratteri, non forzato
9. Proposta sempre revisionabile
10. Nessuna modifica live senza approvazione manuale

## File regole

- `product-seo-rules.md`
- `collection-seo-rules.md`
- `image-alt-rules.md`
- `proposal-rules.md`
- `content-brief-rules.md` (fase futura blog)
- `schema-rules.md` (fase futura structured data)
- `brand-guardrails.md`
- `source-map.md`
