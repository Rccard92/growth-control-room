# Regole Publishing

## Principio fondamentale

**Nessuna pubblicazione automatica su Shopify in questa foundation.**

## Scope OAuth

- `read_content` — sync collections, pages, blogs, articles
- `write_content` — riservato a step futuro (draft controllato)

## Workflow futuro (non implementato ora)

1. Opportunity `planned` → brief `approved`
2. Generazione draft articolo (AI + skill)
3. Review umana obbligatoria
4. Export o publish via Admin API con conferma esplicita
5. Aggiornamento status opportunity/brief

## Cosa fa oggi il modulo

- Sync read-only contenuti
- Audit SEO e opportunità
- Dashboard Content SEO Room
- Persistenza issue/opportunity/brief schema

## Cosa non fa

- Creare/modificare articoli Shopify
- Aggiornare meta prodotto/collection via API
- Schedulare publish
- Inventare metriche Search Console o GA4
