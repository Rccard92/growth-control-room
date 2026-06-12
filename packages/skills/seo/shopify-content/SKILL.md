# Shopify SEO Content Strategist Skill

## Nome

Shopify SEO Content Strategist Skill

## Obiettivo

Analizzare contenuti ecommerce Shopify e generare audit SEO, opportunità editoriali, brief contenuto e suggerimenti di internal linking — senza inventare dati e senza pubblicare automaticamente.

## Input

- Prodotti Shopify (`ShopifyProduct`: title, handle, seo, inventory, raw_payload)
- Collections (`ShopifyCollection`: description, seo, products_count)
- Pages (`ShopifyPage`: body, seo)
- Blogs (`ShopifyBlog`)
- Articles (`ShopifyArticle`: body, seo, tags, author)
- SEO metadata (title, description per entity)
- Performance prodotto da `ShopifyOrderLineItem` (best seller, vendite zero)
- Inventory status (`total_inventory`, variant stock)
- Attribution/source se disponibile su ordini

## Output

- SEO issues (`SeoAuditIssue`)
- Content opportunities (`ContentOpportunity`)
- Blog topic ideas
- Product content improvements
- Collection SEO improvements
- Internal linking suggestions
- Content briefs (`ContentBrief` — struttura, non publish)

## Principi

1. **Non inventare dati** — keyword, volumi e claim devono derivare da catalogo, handle, title o issue rilevate.
2. **Priorità best seller** — prodotti con più vendite e meta/body deboli = alta priorità.
3. **Priorità stock fermo** — prodotti attivi con stock e zero vendite = potenziale contenuto informativo.
4. **Intent di ricerca** — classificare informativo, commerciale, transazionale dove applicabile.
5. **Internal linking** — proporre link verso prodotti e collections reali dello store.
6. **No publish automatico** — tutti i draft richiedono conferma manuale; `write_content` solo in step successivo.

## File regole

- `seo-audit-rules.md` — checklist audit per entity type
- `content-opportunity-rules.md` — tipi e priorità opportunità
- `internal-linking-rules.md` — pattern link e anchor
- `product-content-rules.md` — meta e body prodotto
- `collection-content-rules.md` — pillar collection
- `blog-brief-rules.md` — struttura brief
- `publishing-rules.md` — workflow draft/export controllato

## Integrazione Growth Control Room

- Sync contenuti: `POST /api/projects/{id}/content/seo/sync-shopify`
- Analisi: `POST /api/projects/{id}/content/seo/analyze`
- Dashboard: `GET /api/projects/{id}/content/seo/dashboard`
