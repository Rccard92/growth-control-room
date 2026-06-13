# Changelog

Tutte le modifiche rilevanti a Growth Control Room sono documentate qui.
Il progetto è in fase **Alpha** — versioni `0.x.x-alpha`.

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
