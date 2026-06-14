# Changelog

Tutte le modifiche rilevanti a Growth Control Room sono documentate qui.
Il progetto è in fase **Alpha** — versioni `0.x.x-alpha`.

## [0.3.7-alpha] - 2026-06-13

Tipo: Alpha patch

- Fixed FAQ & Objections import normalization for object-based AI outputs
- Prevented backend 500 on flexible FAQ proposal structures

## [0.3.6-alpha] - 2026-06-13

Tipo: Alpha minor

- Added modular FAQ & Objections section in Brand Intelligence
- Added single-file FAQ import (scoped AI extraction, no auto-save)
- Added FAQ & Objections to BrandContextBuilder (`promptContext.faqObjections`, `fullText`)
- Product SEO can consume FAQ context non-destructively when section is populated

## [0.3.5-alpha] - 2026-06-13

Tipo: Alpha minor

- Added AI Context Preview tab in Brand Intelligence
- Added `previewText` human-friendly output in `promptContext` (AI modules still use `fullText`)
- Moved external source enrichment warnings from Overview to collapsible section in Brand Profile

## [0.3.4-alpha] - 2026-06-13

Tipo: Alpha minor

- Added modular Product Knowledge (general rules + Shopify-linked product items)
- Migration `024`: tables `brand_product_knowledge_general` and `brand_product_knowledge_items`
- Scoped general import from single file; apply-proposal merge without wipe
- BrandContextBuilder exposes `productKnowledge`; Product SEO uses per-product lookup + general fallback
- Overview 6th card; knowledge score averaged over 5 modules

## [0.3.3-alpha] - 2026-06-13

Tipo: Alpha minor

- Added modular Safe Claims & Red Flags section (import file, apply-proposal, manual form)
- Migration `023`: table `brand_safe_claims` (1:1 project)
- BrandContextBuilder: `safeClaims` in bundle and `promptContext`; prudence fallback when empty
- Product SEO guardrails when SAFE CLAIMS block is present in brand context
- Overview 5th card; knowledge score averaged over 4 modules

## [0.3.2-alpha] - 2026-06-13

Tipo: Alpha minor

- Added single-file Brand Identity import (PDF/DOCX/TXT/MD) with scoped AI proposal
- Added Brand Identity apply-proposal flow (preview → confirm → official save)
- Improved machine-ready BrandContextBuilder: `brandContextVersion`, `promptContext`, clean prompt blocks
- Brand Identity UI: upload block + editable AI proposal + official form

## [0.3.1-alpha] - 2026-06-13

Tipo: Alpha minor

- Added modular Brand Identity and Visual Identity sections to Brand Intelligence
- 4-tab UI: Overview, Brand Profile, Brand Identity, Visual Identity
- Migration `022`: tables `brand_identities` and `brand_visual_identities`
- API: GET/PUT identity, GET/PUT visual-identity, extract-from-website, apply-proposal
- `BrandContextBuilder` includes Profile + Identity + Visual in context bundle and prompt
- Overview shows 3 module status cards (complete / partial / empty)

## [0.3.0-alpha] - 2026-06-13

Tipo: Alpha minor / reset controllato

- Simplified Brand Intelligence into Brand Profile v1 (Overview + Brand Profile tab only)
- Removed complex import AI workflow from UI (wizard, brief, facts, section drafts, CRUD tabs)
- Added source-based profile enrichment (`POST .../profile/enrich`) and apply-proposal flow
- `BrandContextBuilder` now uses official Brand Profile as primary context (`primarySource=brand_profile`)
- Migration `021_brand_profile_v1`: social URLs, content notes, enrichment metadata on `brand_profiles`
- Legacy BI endpoints marked deprecated in API; DB migrations 015–020 unchanged

## [0.2.7-alpha] - 2026-06-13

Tipo: Alpha patch

- Fix response Brand Intelligence Brief: campi JSON/list nullable (`source_fact_ids`, ecc.) normalizzati a `[]`
- Mapper `build_brand_intelligence_brief_read` su GET/PATCH/approve/archive brief
- Creazione brief: liste `source_*` sempre array, mai `NULL` in scrittura

## [0.2.6-alpha] - 2026-06-13

Tipo: Alpha minor

- Brand Intelligence Brief Mode: brief flessibile a macro-sezioni come fonte primaria AI
- `brand_intelligence_briefs` (migration 020), synthesis `brief_synthesis.py` senza validazione Pydantic bloccante
- API: generate-brief, CRUD briefs, approve/archive con un solo brief approved per progetto
- `BrandContextBuilder` priorità `primarySource=brand_intelligence_brief`
- Import AI: step 3 centrato sul brief; facts/section drafts in dettagli tecnici
- Batch processor: nessuna auto-synthesis section drafts a fine import

## [0.2.5-alpha] - 2026-06-13

Tipo: Alpha patch

- Salvataggio esplicito fonti brand su batch esistente (`PUT .../sources`)
- Refresh context async: re-fetch fonti, archivia bozze non applicate, rigenera synthesis
- UI: pulsanti Salva fonti / Aggiorna e rigenera, polling progress, auto step 3
- `GET /section-drafts?latestOnly=true` — ultima versione attiva per sezione
- Bozze `applied` e BI ufficiale mai modificati da save/refresh

## [0.2.4-alpha] - 2026-06-13

Tipo: Alpha minor

- Source Enrichment Import AI: brand name, sito web, social e piattaforme recensioni
- `BrandExternalSource` con fetch pubblico leggero (no scraping aggressivo)
- Migration 019: `brand_external_sources`, `source_external_ids` su bozze
- Sintesi source-aware: file + fonti esterne, warning su conflitti
- UI: form Fonti brand, pannello Fonti analizzate, rigenera bozze con fonti esterne

## [0.2.3-alpha] - 2026-06-13

Tipo: Alpha minor

- AI synthesis from imported documents: bozze complete per sezione Brand Intelligence
- `BrandSectionDraft` con review umana prima dell'apply (facts come evidenze)
- Migration 018: `brand_section_drafts`
- Apply non distruttivo: enrich su campi vuoti, conflitti bloccano overwrite
- UI Import AI: griglia bozze per sezione, editor strutturato, review facts opzionale

## [0.2.2-alpha] - 2026-06-13

Tipo: Alpha patch

- Brand Intelligence import batch jobs: `brand_import_batches` persistente, elaborazione async
- Progress tracking su DB con polling frontend ogni 2s
- Conflict detection per import incrementali (`update_mode`, `previous_value`, `conflict_status`)
- Review obbligatoria prima dell'apply — nessun overwrite automatico dei dati approvati
- Migration 017: batch, progress e campi conflict su documents/facts

## [0.2.1-alpha] - 2026-06-13

Tipo: Alpha patch

- AI document import foundation: upload PDF/DOCX/TXT/MD, estrazione testo, classificazione OpenAI
- Extracted facts review workflow con approve/modify/reject/apply
- Onboarding dual-path: compilazione guidata vs Import AI
- Migration 016: `brand_source_documents`, `brand_extracted_facts`
- Nessun auto-save: solo facts approvati entrano nelle tabelle ufficiali

## [0.2.0-alpha] - 2026-06-13

Tipo: Alpha minor

- **Brand Intelligence Foundation**: 10 modelli DB, migration 015, API CRUD completa
- Brand Knowledge Score (9 sezioni pesate, status incomplete/developing/ready)
- `BrandIntelligenceContextBuilder` per contesto AI unificato
- UI: Overview, wizard 7 step, tab per sezione, sidebar e shortcut Control Room
- Integrazione non distruttiva SEO Optimizer (arricchimento prompt, fallback se profilo vuoto)
- Documentazione `docs/brand-intelligence.md` e `docs/ai-architecture.md`

## [0.1.2-alpha] - 2026-06-13

Tipo: Alpha patch

- UX compatta Content SEO Optimizer
- KPI summary prodotti/categorie con score medio
- Rimozione tab Proposte dalla pagina principale
- Feedback sync/analyze dismissible (toast auto-dismiss)
- Miglioramenti visuali tabelle e header Product & Collection SEO

## [0.1.1-alpha] - 2026-06-13

Tipo: Alpha patch

- Product & Collection SEO Optimizer: modal di modifica più leggibile (portal, 720px, footer sticky)
- Campi Shopify precompilati con `currentValues` camelCase
- Badge stato campo: OK / Mancante / Da migliorare
- Flusso AI: preview proposta, copia nel form, nessuna applicazione automatica
- SEO skill pack interno ispirato da claude-seo (MIT)
- Changelog piattaforma e policy di versioning Alpha

## [0.1.0-alpha] - 2026-06-01

Tipo: Alpha minor

- Shopify OAuth connection
- Shopify Sync v2
- Shopify Control Room / E-commerce dashboard
- Content SEO foundation
- Product & Collection SEO Optimizer (score, analisi, proposte, approve/apply)
