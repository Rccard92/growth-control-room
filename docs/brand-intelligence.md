# Brand Intelligence

Brand Intelligence è la knowledge base strutturata del brand in Growth Control Room. Ogni progetto ha un profilo brand che alimenta i moduli AI (SEO, futuri PED/Ads/Email) con contesto coerente, compliance e voice.

## Onboarding

All'apertura di un progetto nuovo o con score basso, l'Overview propone due percorsi:

1. **Compilazione guidata** — wizard manuale con sole informazioni obbligatorie minime
2. **Importa da file con AI** — upload PDF/DOCX/TXT/MD, estrazione testo, classificazione OpenAI, review umana

Le sezioni avanzate restano compilabili nelle tab dedicate per migliorare lo score.

## AI File Import v1

### Flusso

1. **Upload** — `POST .../sources/upload` (multipart, max 10 file, 15MB ciascuno)
2. **Estrazione testo** — sincrona al upload (pypdf, python-docx); storage alpha: `text_only` (metadata + testo, no binario)
3. **Estrazione AI** — `POST .../sources/{id}/extract` o batch; crea `BrandExtractedFact` con `status=suggested`
4. **Review umana** — approva, modifica, sposta sezione o rifiuta ogni fact
5. **Apply** — `POST .../extracted-facts/apply` salva **solo** facts `approved` nelle tabelle ufficiali

### Regola fondamentale

Le estrazioni AI sono **suggestions**, non dati ufficiali. `BrandIntelligenceContextBuilder` legge solo le tabelle CRUD ufficiali — i facts non approvati non entrano nel contesto AI.

## Sezioni

| Sezione | Obbligatoria (score minimo) | Descrizione |
|---------|----------------------------|-------------|
| Brand Profile | Sì | Nome, descrizione, settore, storia |
| Voice & Tone | Sì | Tono, stile, parole da usare/evitare |
| Products & Categories | Sì | Almeno 1 prodotto/categoria con nome + descrizione |
| Audience | Consigliata | Segmenti di pubblico |
| Claims & Compliance | Sì | Almeno 1 claim `forbidden` o `caution` |
| SEO Strategy | Consigliata | Keyword primarie |
| Content Pillars | Consigliata | Pilastri editoriali |
| AI Guardrails | Sì | Almeno 1 regola `must_not` |
| Assets | Opzionale | Logo, colori, font (bonus score) |

## Brand Knowledge Score

Punteggio 0–100 calcolato come media pesata delle 9 sezioni:

- **incomplete** (&lt; 60): profilo insufficiente per AI on-brand
- **developing** (60–79): utilizzabile con lacune
- **ready** (≥ 80): profilo maturo per generazione contenuti

Riflette solo dati ufficiali (post-apply). L'endpoint `GET /api/projects/{id}/brand-intelligence/score` restituisce score, sezioni, campi mancanti e raccomandazioni.

## Uso AI

`BrandIntelligenceContextBuilder.build_brand_context(project_id)` è la **fonte unica** del contesto brand per tutti i moduli AI.

- **SEO Optimizer (v1)**: integrazione opzionale — se il profilo è vuoto o score &lt; 10, il prompt SEO resta invariato (fallback).
- **Moduli futuri** (PED, Ads, Email): il contesto brand sarà **obbligatorio** prima della generazione.

## API

Base path: `/api/projects/{project_id}/brand-intelligence`

**CRUD ufficiale:** overview, score, context, profile, voice, products, audience, claims, seo-strategy, pillars, guardrails, assets

**Import AI:**

- `POST /sources/upload` — multipart `files[]`
- `GET /sources` — lista documenti
- `POST /sources/{document_id}/extract` — estrazione AI singola
- `POST /sources/extract-batch` — `{ documentIds: [] }`
- `GET /extracted-facts` — query: `status`, `targetSection`, `sourceDocumentId`
- `PATCH /extracted-facts/{fact_id}` — review
- `POST /extracted-facts/apply` — `{ factIds: [] }` solo approved

## UI

Sidebar progetto → **Brand Intelligence** (dopo Control Room).

- **Overview**: onboarding dual-path, score ring, sezioni
- **Wizard**: minimo obbligatorio
- **Import AI**: 3 step (carica → estrai → revisiona)
- **Documenti**: elenco file caricati
- **Tab per sezione**: CRUD manuale

Route import: `/projects/:id/brand-intelligence/import`

## Migration

- `015_brand_intelligence_foundation` — 10 tabelle CRUD
- `016_brand_intelligence_ai_import` — `brand_source_documents`, `brand_extracted_facts`
