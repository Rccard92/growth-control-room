# Source map — gcr-editorial-article

| Regola | Origine |
|--------|---------|
| Limiti H2/H3/parole per tipo | GCR custom — allineato a `editorial_structure_profiles.py` |
| Paragrafi brevi, liste, scanability | GCR custom + best practice content UX |
| Box HTML GCR (`gcr-article-note`, `gcr-product-tip`) | GCR custom v1 |
| Neuromarketing etico | GCR custom — ispirato a FAQ/objections BI |
| Tag HTML whitelist | GCR custom — allineato a `html_sanitize.py` |
| Internal linking conservativo | GCR custom + `shopify-content` reference (no URL inventati) |
| FAQ brevi max 3 | GCR custom — allineato a brief enforce |
| Safe Claims priorità | GCR Brand Intelligence — non da skill pack |
| Brand guardrails | `gcr-shopify-seo/brand-guardrails.md` (caricato separatamente) |
| Content brief SEO base | `gcr-shopify-seo/content-brief-rules.md` (caricato separatamente) |

## Reference (non runtime)

- `packages/skills/seo/shopify-content/` — audit editoriale, internal linking strategy
- `packages/skills/external/claude-seo/imported-skills/seo-content-brief/` — content brief MIT

## Versione

- **v1.1** — 2026-06-13 — raffinamento post-test Shopify (grassetti 6–9, gcr-article-body, link verificati, CTA strutturata, Safe Claims precisi)
- **v1** — 2026-06-13 — prima release Editorial Article Skill Pack
