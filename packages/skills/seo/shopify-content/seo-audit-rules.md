# Regole SEO Audit

## Prodotti

| issue_type | severity | Condizione |
|------------|----------|------------|
| missing_meta_title | critical | `seo_title` vuoto su prodotto ACTIVE |
| missing_meta_description | critical | `seo_description` vuoto su prodotto ACTIVE |
| short_meta_title | warning | meta title < 30 caratteri |
| weak_product_body | warning | description/body in raw_payload assente o < 100 caratteri testo |
| active_no_sales_with_stock | opportunity | ACTIVE, inventory > 0, zero vendite nel periodo |
| bestseller_no_blog_link | opportunity | top vendite senza articolo che linka handle/URL prodotto |

## Collections

| issue_type | severity | Condizione |
|------------|----------|------------|
| missing_description | critical | description_text vuota o < 50 caratteri |
| missing_meta_title | warning | seo_title vuoto |
| missing_meta_description | warning | seo_description vuoto |
| no_linked_article | opportunity | nessun articolo con link a collection handle |

## Pages

| issue_type | severity | Condizione |
|------------|----------|------------|
| weak_title | warning | title vuoto o < 10 caratteri |
| missing_meta_description | warning | seo_description vuoto |
| short_body | warning | body_text < 150 caratteri |

## Articles

| issue_type | severity | Condizione |
|------------|----------|------------|
| missing_meta_title | warning | seo_title vuoto |
| missing_meta_description | warning | seo_description vuoto |
| short_body | warning | body_text < 300 caratteri |
| no_internal_product_links | opportunity | body senza link a /products/ |
| no_internal_collection_links | opportunity | body senza link a /collections/ |
| missing_faq_section | info | body > 800 char, intent informativo, nessuna sezione FAQ |

## Status issue

- `open` — generata da analyze, da affrontare
- `ignored` — esclusa manualmente (futuro)
- `resolved` — risolta (futuro)
