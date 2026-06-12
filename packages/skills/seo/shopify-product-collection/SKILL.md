# Shopify Product & Collection SEO Optimizer Skill

## Nome

Shopify Product & Collection SEO Optimizer Skill

## Obiettivo

Analizzare prodotti e collections Shopify con score rule-based, generare proposte SEO revisionabili e applicare modifiche solo dopo approvazione manuale.

## Input

- Prodotti sincronizzati (`ShopifyProduct`: title, handle, seo, tags, description, media, inventory)
- Collections sincronizzate (`ShopifyCollection`: title, handle, description, seo, image)
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
6. Distinguere SEO title da titolo prodotto
7. Meta description persuasiva ma realistica
8. Alt text descrittivo, non forzato
9. Proposta sempre revisionabile
10. Nessuna modifica live senza approvazione manuale

## File regole

- `product-seo-score-rules.md`
- `collection-seo-score-rules.md`
- `image-alt-rules.md`
- `seo-proposal-rules.md`
- `approval-workflow-rules.md`
- `brand-guardrails.md`
