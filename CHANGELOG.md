# Changelog

Tutte le modifiche rilevanti a Growth Control Room sono documentate qui.
Il progetto è in fase **Alpha** — versioni `0.x.x-alpha`.

## [0.5.12-alpha] - 2026-06-13

Tipo: Alpha patch

- Fixed frontend Railway build by syncing pnpm lockfile after web dependency changes

## [0.5.11-alpha] - 2026-06-13

Tipo: Alpha patch

- Fixed frontend handling of 204 No Content API responses
- Editorial item deletion no longer shows JSON parse errors
- Calendar refreshes correctly after deleting editorial content

## [0.5.10-alpha] - 2026-06-13

Tipo: Alpha patch

- Stabilized product and collection image ALT generation
- Added robust per-image ALT generation handling
- Fixed image ALT values disappearing after apply
- Improved Shopify/non-Shopify image state feedback

## [0.5.9-alpha] - 2026-06-13

Tipo: Alpha patch

- Fixed AiRequestMetadata UUID coercion
- Product SEO AI generation no longer fails when entity_id is a UUID
- Hardened AI metadata handling across all generators

## [0.5.8-alpha] - 2026-06-13

Tipo: Alpha patch

- Fixed AI generation failures after model settings routing
- Centralized OpenAI request parameter compatibility for GPT-5.x models
- Added better OpenAI 400 error logging and UI feedback
- Ensured Product SEO, Brand Intelligence and Blog generators use operation-level model settings
- Added validate-model endpoint and Test modello in Model Settings UI

## [0.5.7-alpha] - 2026-06-13

Tipo: Alpha patch

- Fixed AI Model Settings save payload (PUT sends JSON object with correct Content-Type)
- Model changes now persist correctly from the UI
- Improved error feedback for invalid model setting requests

## [0.5.6-alpha] - 2026-06-13

Tipo: Alpha patch

- Simplified AI Model Settings UI renamed to Modelli AI with category accordions
- Added GCR recommended model and reason per AI operation in registry
- Added bulk actions: Applica consigli GCR, Ripristina da Railway, Salva tutte
- Consolidated pricing warnings into single banner; added GPT-5.x model pricing
- Technical fields (tier, tokens, source) moved to expandable Avanzate section

## [0.5.5-alpha] - 2026-06-13

Tipo: Alpha patch

- Fixed AI Model Settings response validation (GET `/ai-model-settings` no longer 500)
- Normalized camelCase/snake_case mapping for model settings (internal snake_case, API camelCase output)
- Improved empty state for AI Costs overview when no tracked requests in period
- Clarified Railway model env variables are fallback/seed only, not global runtime override

## [0.5.4-alpha] - 2026-06-13

Tipo: Alpha patch

- Added configurable AI Model Settings panel in AI Costs (per-operation model/tier/tokens/temperature)
- Added AI Operation Registry with implemented and planned operation keys
- Model routing resolves from project/global DB settings before env fallback
- Fixed AI Usage summary 500: routingInsights camelCase/snake_case schema mismatch
- Extended AiUsageLog with operation_key; summary breakdown byOperationKey
- Migration 033: ai_model_settings table

## [0.5.3-alpha] - 2026-06-13

Tipo: Alpha patch

- Added centralized AI Model Routing (`model_policy.py`) with 5 tiers: cheap, standard, premium, reasoning, fallback
- Model resolved from context profile + metadata; services no longer choose OpenAI models
- Extended `ai_client` with max_tokens, temperature, optional schema-error retry to standard tier
- Extended `AiUsageLog` with model tier, policy source, requested model, max tokens, temperature
- AI Costs page: tier column, tier filter, Model Routing Insights (cost/requests per tier + warnings)
- New env vars: `OPENAI_MODEL_CHEAP/STANDARD/PREMIUM/REASONING/FALLBACK`, `AI_ALLOW_MODEL_OVERRIDE`, `AI_ENABLE_MODEL_FALLBACK_ON_SCHEMA_ERROR`
- Docs: AI Model Routing section in `ai-architecture.md`, new `cost-optimization.md`

## [0.5.2-alpha] - 2026-06-13

Tipo: Alpha patch

- Added AI Context Profiles
- Reduced unnecessary Brand Intelligence payloads per AI task
- Added context profile metadata to AI Usage Monitor
- Prepared prompt structure for better caching and lower token usage

## [0.5.1-alpha] - 2026-06-13

Tipo: Alpha patch

- Fixed AI Usage Monitor timezone handling
- Budget status no longer crashes with aware datetime filters

## [0.5.0-alpha] - 2026-06-13

Tipo: Alpha minor

- Added AI Usage Monitor (AI Costs page)
- Added centralized OpenAI client (`ai_client.py`) with automatic usage logging
- Added AI token and estimated cost tracking per project/module/operation
- Added project-level AI budget guardrails (daily/monthly env limits)
- Added compact brand context builder and prompt cache keys for AI tasks

## [0.4.9-alpha] - 2026-06-13

Tipo: Alpha patch

- Fixed Changelog page version source
- Removed duplicated AI reasoning helper text in Product/Collection SEO fields
- Fixed collection image alt accept action

## [0.4.8-alpha] - 2026-06-13

Tipo: Alpha patch

- Blog Brief Generator now uses Editorial Guidelines (optional author suggestion workflow)
- `brief_payload` extended with `authorSuggestion`, `authorReason`, `contentLengthProfile`, `communityCtaSuggestion`, `editorialToneNotes`
- Article Generator respects brief author choice — no forced brand signature when `authorSuggestion` is empty
- Article preview shows author only when `authorName` is set

## [0.4.7-alpha] - 2026-06-13

Tipo: Alpha patch

- Added Brand Intelligence **Editorial Guidelines** section (DB, API, UI, AI context)
- Article Generator uses Editorial Guidelines for shorter, human, community-oriented drafts
- Extended `article_payload` with author signature, community CTA, reading time and length profile
- Safe Claims remain absolute priority over editorial tone

## [0.4.6-alpha] - 2026-06-14

Tipo: Alpha patch

- Fixed Brief SEO textarea styling (dark theme coerente)
- Added Article & Preview tab in editorial item modal
- Added single article draft generation from approved brief
- Added rendered article preview with HTML sanitization
- Shopify publishing remains disabled for future step

## [0.4.5-alpha] - 2026-06-13

Tipo: Alpha patch

- Added tabbed editorial item modal (Dettaglio / Brief SEO)
- Improved Brief SEO layout with sectioned cards
- Added auto-resize textarea component
- Added batch brief generation with progress tracking

## [0.4.4-alpha] - 2026-06-13

Tipo: Alpha patch

- Improved compact editorial date picker
- Replaced editorial item drawer with centered modal
- Removed redundant status legend from editorial calendar
- Added optional cascade rescheduling for editorial items

## [0.4.3-alpha] - 2026-06-13

Tipo: Alpha patch

- Fixed editorial plan payload serialization
- Added custom dark date picker
- Added custom checkbox component
- Added multi-objective editorial planning
- Made keywords and notes optional

## [0.4.2-alpha] - 2026-06-13

Tipo: Alpha patch

- Replaced editorial plan drawer with centered modal (opaque overlay, no side drawer)
- Added reusable AppModal component for centered dialogs
- Added reusable dark AppSelect component with portal menu
- Improved dropdown consistency in Content SEO wizard/drawer and Brand Intelligence Product Knowledge

## [0.4.1-alpha] - 2026-06-13

Tipo: Alpha minor

- Added Blog & Ricette Brief Generator (single-item, OpenAI + Brand Intelligence context)
- Added editable SEO brief payload stored on `ContentSeoEditorialItem.brief_payload`
- Added brief approval workflow (`brief_pending` → `brief_approved`) via drawer UI
- Blog article generation and Shopify publish remain disabled for future steps

## [0.4.0-alpha] - 2026-06-13

Tipo: Alpha minor

- Split Content SEO in due tab: Prodotti & Categorie (optimizer esistente) e Blog & Ricette (calendario editoriale)
- Nuovo modello `ContentSeoEditorialItem` e migration `027` per calendario blog/ricette
- API CRUD editorial-items + generazione piano rule-based (`generate-calendar`, supporto `dryRun`)
- UI calendario mensile, wizard 4 step, drawer item con CTA brief disabilitata
- Blog & Ricette accessibile senza Shopify; prodotti opzionali nel wizard
- Documentazione `docs/content-seo.md` e sezione Brief Generator futuro in `docs/ai-architecture.md`

## [0.3.8-alpha] - 2026-06-13

Tipo: Alpha patch

- Fixed legacy FAQ & Objections dict normalization
- Prevented Brand Intelligence Overview and AI Context crashes from mixed FAQ data
- Added defensive normalization for FAQ context and score calculation
- Added Alembic migration to repair existing FAQ JSONB data

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
