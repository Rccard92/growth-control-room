# Content SEO

Modulo **Content SEO** del Growth Control Room: ottimizzazione Shopify (prodotti e categorie) e pianificazione editoriale blog/ricette.

Versione corrente: **0.4.1-alpha** (Brief Generator).

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

**Non generato in questo step:** articolo completo, body HTML, immagini, publish Shopify.

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

Nessun endpoint editorial richiede Shopify connesso.

## Database

Tabella: `content_seo_editorial_items` (migration `027`).

Modello: `ContentSeoEditorialItem` — FK `project_id`, indici su `planned_date`, `status`, `content_type`. Campo JSONB `brief_payload` per brief SEO; `article_payload` riservato ad Article Generator.

## Roadmap (step successivi)

1. **Article Generator** — bozze lunghe da brief con `brief_approved`
2. **Shopify Publisher** — draft blog/article su Shopify
3. **Sync/analyze SEO blog** — audit contenuti blog esistenti

## Test manuali

1. Tab Prodotti & Categorie → optimizer invariato con Shopify connesso
2. Tab Blog & Ricette → calendario mese corrente, oggi evidenziato
3. Crea piano editoriale → wizard → anteprima → conferma → item nel calendario
4. Click item → modifica → salva → persistenza dopo reload
5. Validazioni: date invertite, zero tipi, custom senza giorni → errori leggibili
6. Senza Shopify: wizard OK, prodotti disabilitati/empty state
7. Genera brief su item → modifica meta/struttura → salva → reload → approva → badge «Brief approvato»
