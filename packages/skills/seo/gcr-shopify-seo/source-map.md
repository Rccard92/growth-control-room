# Source Map — GCR Shopify SEO Skill

Tracciabilità regole: origine claude-seo (MIT), custom GCR, custom Shopify.

| Regola GCR | Origine | File GCR | Note |
|------------|---------|----------|------|
| Product title min 10 char | GCR custom | product-seo-rules.md | Allineato `TITLE_MIN` |
| SEO title 30–60 char | claude-seo seo-ecommerce | product-seo-rules.md | Adattato Shopify metafields |
| Meta description 120–160 char | claude-seo seo-ecommerce | product-seo-rules.md | |
| Description body ≥ 150 char | GCR custom | product-seo-rules.md | |
| Handle kebab-case | GCR custom + ecommerce | product-seo-rules.md | |
| Tags 1–10 coerenti | GCR custom | product-seo-rules.md | |
| Pesi score 15/20/20/15/10/10/10 | GCR custom | product-seo-rules.md | `PRODUCT_WEIGHTS` |
| Collection description peso 25 | GCR custom | collection-seo-rules.md | `COLLECTION_WEIGHTS` |
| Alt 10–125 char, descrittivo | claude-seo seo-images | image-alt-rules.md | |
| Tipi immagine prodotto/packaging/dettaglio/lifestyle | GCR custom | image-alt-rules.md | |
| No keyword stuffing alt | claude-seo seo-images | image-alt-rules.md | |
| Product title vs SEO title split | claude-seo seo-ecommerce | proposal-rules.md | |
| Proposal JSON schema runtime | GCR custom | proposal-rules.md | Allineato API |
| No claim inventati | GCR custom | proposal-rules.md, brand-guardrails.md | |
| Draft → approve → apply | GCR custom | proposal-rules.md | |
| Best-seller severity boost | GCR custom | product-seo-rules.md | `product_seo_analyzer` |
| Search intent classification | claude-seo seo-content-brief | content-brief-rules.md | Futuro blog |
| Outline H2/H3 | claude-seo seo-content-brief | content-brief-rules.md | Futuro |
| E-E-A-T / information gain | claude-seo seo-content-brief | content-brief-rules.md | Futuro |
| Product JSON-LD | claude-seo seo-schema | schema-rules.md | Futuro |
| BreadcrumbList schema | claude-seo seo-schema | schema-rules.md | Futuro |
| Keyword cluster hub-spoke | claude-seo seo-cluster | — | Futuro, reference only |
| Solmielato tone/claims | GCR custom placeholder | brand-guardrails.md | Da configurare per progetto |
| Internal linking prodotti | claude-seo seo-ecommerce | product/collection-seo-rules.md | Futuro |

## External reference paths

- `packages/skills/external/claude-seo/imported-skills/seo-ecommerce/`
- `packages/skills/external/claude-seo/imported-skills/seo-images/`
- `packages/skills/external/claude-seo/imported-skills/seo-content-brief/`
- `packages/skills/external/claude-seo/imported-skills/seo-schema/`
- `packages/skills/external/claude-seo/imported-skills/seo-cluster/`

## Runtime pack

`packages/skills/seo/gcr-shopify-seo/` — caricato da `seo_skill_loader.py`
