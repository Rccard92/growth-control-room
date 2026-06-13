# Brand Intelligence

Brand Intelligence è la knowledge base strutturata del brand in Growth Control Room. Ogni progetto ha un profilo brand che alimenta i moduli AI (SEO, futuri PED/Ads/Email) con contesto coerente, compliance e voice.

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

L'endpoint `GET /api/projects/{id}/brand-intelligence/score` restituisce score, sezioni, campi mancanti e raccomandazioni.

## Uso AI

`BrandIntelligenceContextBuilder.build_brand_context(project_id)` è la **fonte unica** del contesto brand per tutti i moduli AI.

- **SEO Optimizer (v1)**: integrazione opzionale — se il profilo è vuoto o score &lt; 10, il prompt SEO resta invariato (fallback).
- **Moduli futuri** (PED, Ads, Email): il contesto brand sarà **obbligatorio** prima della generazione.

Il metodo `format_for_prompt()` produce un blocco compatto `# Brand Intelligence` da appendere al system prompt.

## API

Base path: `/api/projects/{project_id}/brand-intelligence`

- `GET /` — overview + score
- `GET /score` — solo score
- `GET /context` — bundle completo per moduli AI
- `GET/PUT /profile`, `/voice`, `/seo-strategy`
- `GET/POST/PUT/DELETE` per products, audience, claims, content-pillars, guardrails, assets

## UI

Sidebar progetto → **Brand Intelligence** (dopo Control Room).

- **Overview**: score ring, stato sezioni, CTA wizard
- **Wizard**: 7 step guidati con salvataggio progressivo
- **Tab per sezione**: CRUD manuale
- **Sources**: placeholder (upload documenti in roadmap)

## Migration

`015_brand_intelligence_foundation` — 10 tabelle con FK `projects.id` CASCADE.
