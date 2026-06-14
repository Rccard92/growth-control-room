# Content SEO

Modulo **Content SEO** del Growth Control Room: ottimizzazione Shopify (prodotti e categorie) e pianificazione editoriale blog/ricette.

Versione corrente: **0.4.0-alpha** (foundation editoriale).

## Struttura UI

La pagina `/projects/{id}/content` è divisa in due tab a livello pagina:

| Tab | Contenuto | Requisiti |
|-----|-----------|-----------|
| **Prodotti & Categorie** | SEO Optimizer esistente (sync, analisi, proposte, apply) | Shopify connesso |
| **Blog & Ricette** | Calendario editoriale, wizard piano, drawer item | Nessun gate Shopify |

Il gate Shopify si applica **solo** alla tab Prodotti. Blog & Ricette è accessibile sempre; i prodotti nel wizard sono opzionali.

## Blog & Ricette — workflow

### Stati item (`ContentSeoEditorialStatus`)

| Stato | Significato |
|-------|-------------|
| `idea` | Idea iniziale, senza brief |
| `brief_pending` | In attesa di generazione brief |
| `brief_approved` | Brief approvato |
| `draft_pending` | Bozza articolo in attesa |
| `draft_review` | Bozza in revisione |
| `ready_to_publish` | Pronto per pubblicazione |
| `scheduled` | Programmato |
| `published` | Pubblicato |
| `publish_error` | Errore in pubblicazione |

### Tipologie contenuto

- `educational_article` — Articolo educativo
- `product_guide` — Guida prodotto
- `recipe` — Ricetta
- `faq_objection_article` — FAQ/obiezione in articolo
- `product_comparison` — Confronto tra prodotti
- `seasonal_article` — Articolo stagionale
- `brand_storytelling` — Storytelling brand/prodotto

### Calendario mensile

- Vista mese corrente (`YYYY-MM`) con navigazione ◀ ▶
- Giorno odierno evidenziato (`.editorial-calendar__day--today`)
- Card per item: titolo, tipologia, badge stato, prodotto collegato (se presente)
- Click su card → drawer dettaglio/edit

### Wizard «Crea piano editoriale»

1. **Periodo e frequenza** — date, `frequency`, giorni preferiti (obbligatori per `custom` e `twice_weekly`)
2. **Tipologie** — almeno un content type
3. **Obiettivo e intensità commerciale**
4. **Prodotti, keyword, note** — multi-select prodotti Shopify (se connesso), keyword, note
5. **Anteprima** — `POST generate-calendar?dryRun=true`
6. **Conferma** — `dryRun=false`, item persistiti nel DB

La generazione è **rule-based** (nessuna chiamata OpenAI): titoli placeholder da template, rotazione tipologie sulle date, status `brief_pending` se ci sono keyword.

### Drawer item

Campi editabili: titolo, data, stato, obiettivo, keyword, note. CTA **«Genera brief — prossimo step»** disabilitata (futuro Brief Generator).

## API

Base: `/api/projects/{project_id}/content/seo/`

| Metodo | Path | Note |
|--------|------|------|
| GET | `editorial-items` | Query: `month`, `status`, `contentType` |
| POST | `editorial-items` | Crea item manuale |
| GET | `editorial-items/{item_id}` | Dettaglio |
| PUT | `editorial-items/{item_id}` | Update |
| DELETE | `editorial-items/{item_id}` | Delete |
| POST | `editorial-plan/generate-calendar` | Body wizard; `?dryRun=true` per anteprima |

Nessun endpoint editorial richiede Shopify connesso.

## Database

Tabella: `content_seo_editorial_items` (migration `027`).

Modello: `ContentSeoEditorialItem` — FK `project_id`, indici su `planned_date`, `status`, `content_type`. Campi JSONB `brief_payload` / `article_payload` riservati a step futuri.

## Roadmap (non in 0.4.0-alpha)

1. **Brief Generator** — OpenAI + `BrandContextBuilder` + Safe Claims; approvazione obbligatoria
2. **Article Generator** — bozze lunghe da brief approvato
3. **Shopify Publisher** — draft blog/article su Shopify
4. **Sync/analyze SEO blog** — audit contenuti blog esistenti

## Test manuali

1. Tab Prodotti & Categorie → optimizer invariato con Shopify connesso
2. Tab Blog & Ricette → calendario mese corrente, oggi evidenziato
3. Crea piano editoriale → wizard → anteprima → conferma → item nel calendario
4. Click item → modifica → salva → persistenza dopo reload
5. Validazioni: date invertite, zero tipi, custom senza giorni → errori leggibili
6. Senza Shopify: wizard OK, prodotti disabilitati/empty state
