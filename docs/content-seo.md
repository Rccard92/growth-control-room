# Content SEO

Modulo **Content SEO** del Growth Control Room: ottimizzazione Shopify (prodotti e categorie) e pianificazione editoriale blog/ricette.

Versione corrente: **0.4.6-alpha** (Article Draft Generator).

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

Campi editabili: titolo, data, stato, obiettivo, keyword, note.

### Brief Generator (0.4.1-alpha)

Workflow: **calendario → genera brief → modifica → salva → approva**.

1. Apri item dal calendario → **Genera brief** (singolo item, no bulk)
2. Backend usa `BrandIntelligenceContextBuilder` + Product Knowledge prodotto collegato
3. Brief salvato in `brief_payload` JSONB sull'item; status → `brief_pending`
4. Editor nel drawer: titolo proposto, intento, struttura H2/H3, meta, claim, FAQ, warning
5. **Salva brief** — persiste modifiche senza cambiare status (opzionale)
6. **Approva brief** — `PUT brief` con `status: brief_approved`
7. **Rigenera brief** — conferma se ci sono modifiche non salvate

**Non generato in questo step:** immagini, publish Shopify.

#### Struttura `brief_payload`

```json
{
  "proposedTitle": "",
  "searchIntent": "",
  "targetAudience": "",
  "primaryKeyword": "",
  "secondaryKeywords": [],
  "contentAngle": "",
  "h2H3Structure": [],
  "productsToLink": [],
  "faqToInclude": [],
  "claimsToAvoid": [],
  "safeClaimsToUse": [],
  "recommendedCta": "",
  "metaTitle": "",
  "metaDescription": "",
  "internalLinksSuggestions": [],
  "notes": "",
  "brandContextUsed": [],
  "warnings": []
}
```

### Article Draft Generator (0.4.6-alpha)

Workflow: **brief approvato → genera articolo → modifica → salva bozza → anteprima → segna pronto per pubblicazione**.

**Prerequisito:** item con `status: brief_approved` e `brief_payload` valorizzato.

1. Tab **Articolo & Anteprima** nel modal item
2. **Genera articolo** — `POST editorial-items/{id}/generate-article`
3. Backend usa `BrandIntelligenceContextBuilder` + brief approvato come fonte principale + Product Knowledge prodotto collegato
4. Articolo salvato in `article_payload` JSONB; status → `draft_review`
5. Editor: titolo, handle, excerpt, body HTML/Markdown, SEO meta, tags, CTA
6. **Anteprima**: `bodyHtml` renderizzato (sanitizzato whitelist client-side + backend in save/generate)
7. **Salva bozza articolo** — `PUT article` mantiene `draft_review`
8. **Segna pronto per pubblicazione** — `PUT article` con `status: ready_to_publish`

**Non implementato:** pubblicazione Shopify, scheduling, batch articoli, generazione immagini.

#### Struttura `article_payload`

```json
{
  "title": "",
  "handle": "",
  "excerpt": "",
  "bodyHtml": "",
  "bodyMarkdown": "",
  "seoTitle": "",
  "metaDescription": "",
  "tags": [],
  "linkedProducts": [],
  "cta": "",
  "status": "draft",
  "warnings": [],
  "brandContextUsed": [],
  "generatedAt": ""
}
```

`bodyHtml` è il contenuto principale per anteprima e futura pubblicazione Shopify.

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
| POST | `editorial-items/{item_id}/generate-brief` | Genera brief AI per singolo item |
| PUT | `editorial-items/{item_id}/brief` | Salva/approva `briefPayload`; `status` opzionale (`brief_pending` \| `brief_approved`) |
| POST | `editorial-items/{item_id}/generate-article` | Genera bozza articolo da brief approvato |
| PUT | `editorial-items/{item_id}/article` | Salva `articlePayload`; `status` opzionale (`draft_pending` \| `draft_review` \| `ready_to_publish`) |

Nessun endpoint editorial richiede Shopify connesso.

## Database

Tabella: `content_seo_editorial_items` (migration `027`).

Modello: `ContentSeoEditorialItem` — FK `project_id`, indici su `planned_date`, `status`, `content_type`. Campi JSONB `brief_payload` (brief SEO) e `article_payload` (bozza articolo).

## Roadmap (step successivi)

1. **Shopify Publisher** — draft blog/article su Shopify con conferma esplicita
2. **Sync/analyze SEO blog** — audit contenuti blog esistenti
3. **Batch article generation** — generazione massiva bozze (dopo validazione singolo articolo)

## Test manuali

1. Tab Prodotti & Categorie → optimizer invariato con Shopify connesso
2. Tab Blog & Ricette → calendario mese corrente, oggi evidenziato
3. Crea piano editoriale → wizard → anteprima → conferma → item nel calendario
4. Click item → modifica → salva → persistenza dopo reload
5. Validazioni: date invertite, zero tipi, custom senza giorni → errori leggibili
6. Senza Shopify: wizard OK, prodotti disabilitati/empty state
7. Genera brief su item → modifica meta/struttura → salva → reload → approva → badge «Brief approvato»
8. Tab Articolo & Anteprima → genera articolo → editor + anteprima HTML → salva bozza → segna pronto per pubblicazione → badge calendario aggiornato
