# Changelog

Tutte le modifiche rilevanti a Growth Control Room sono documentate qui.
Il progetto è in fase **Alpha** — versioni `0.x.x-alpha`.

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
