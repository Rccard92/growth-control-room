# Collection SEO Rules (Shopify)

Adattato da claude-seo `seo-ecommerce` per Shopify collections in GCR.

## Campi Shopify analizzati

| Campo | Fonte | Ruolo SEO |
|-------|-------|-----------|
| `title` | Collection title | Nome categoria / pillar |
| `handle` | URL slug | Path categoria |
| `seo_title` | metafields global title_tag | Title tag SERP |
| `seo_description` | metafields global description_tag | Meta description |
| `descriptionHtml` / `description_text` | body collection | Testo categoria, keyword pillar |
| `image_alt` | featured image alt | Image SEO collection |
| `products_count` | prodotti nella collection | Opportunità pillar content |

## Componenti score (pesi GCR)

| Componente | Peso | Ottimo | Warning | Critico |
|------------|------|--------|---------|---------|
| score_title | 15 | title chiaro | generico | assente |
| score_handle | 10 | kebab-case leggibile | corto | assente |
| score_description | 25 | ≥ 150 char testo | 50–149 | < 50 |
| score_seo_title | 20 | 30–60 char | fuori range | assente |
| score_meta_description | 20 | 120–160 char | fuori range | assente |
| score_image_alt | 10 | alt presente | generico | assente |

Implementazione runtime: `seo_scoring_engine.py` + `seo_scoring_constants.py`.

## Regole title

- [ ] Nome categoria chiaro e specifico
- [ ] Distinto da SEO title se necessario per SERP
- [ ] Coerente con prodotti contenuti

## Regole SEO title

- [ ] 30–60 caratteri
- [ ] Può includere brand + categoria + beneficio breve
- [ ] Formato: `[Category] | [Brand]` o `[Category] - [Benefit] | [Brand]`

## Regole meta description

- [ ] 120–160 caratteri
- [ ] Descrive la gamma prodotti nella collection
- [ ] CTA naturale verso esplorazione catalogo

## Regole description (category text)

- [ ] ≥ 150 caratteri testo plain
- [ ] Spiega cosa trova l'utente nella categoria
- [ ] Opportunità pillar: collection con `products_count` ≥ 3 e description debole → recommendation testo categoria più ricco (no blog in v1)

## Regole handle

- [ ] Kebab-case leggibile
- [ ] Keyword categoria nel path senza stuffing

## Regole image alt

- [ ] Alt presente su immagine collection
- [ ] Descrive la categoria o hero visivo (vedi `image-alt-rules.md`)

## Internal linking (futuro)

- [ ] Link verso prodotti principali della collection
- [ ] Breadcrumb verso homepage e sottocategorie
- [ ] Anchor text descrittivo (non "clicca qui")

## Severity

Stesse soglie prodotto: good ≥80, opportunity 60–79, warning 40–59, critical <40.
