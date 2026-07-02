# claude-seo — Imported Reference Pack

## Source repository

- **Repository:** [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo)
- **Import commit:** `47df91ed587f731c11c5c1ff515bdc6c26f48761`
- **License:** MIT (see [LICENSE](./LICENSE))

## Purpose in Growth Control Room

These files are **reference material only**. They are not loaded as a Claude Code plugin runtime.
Growth Control Room adapts selected rules into the internal skill pack at
`packages/skills/seo/gcr-shopify-seo/`.

## Imported skills (this phase)

| Skill | Path | Used in GCR |
|-------|------|-------------|
| seo-ecommerce | `imported-skills/seo-ecommerce/` | Product & collection SEO rules |
| seo-images | `imported-skills/seo-images/` | Image alt text rules |
| seo-content-brief | `imported-skills/seo-content-brief/` | Future blog/editorial briefs |
| seo-schema | `imported-skills/seo-schema/` | Future structured data |
| seo-cluster | `imported-skills/seo-cluster/` | Future keyword clustering |

## GCR skill catalog

`skill-catalog.json` in this directory is the **internal Growth Control Room catalog** of upstream Claude SEO skills.
It exposes structured metadata (status, runtime, integrations, output schema) for the API route
`GET /projects/{project_id}/seo-skills/catalog` and shared TypeScript types in `packages/shared`.
This catalog is read-only metadata only; it does not load or execute Claude Code plugin runtime.

## Not used in GCR v1

The following capabilities from the upstream project are **intentionally excluded**:

- DataForSEO Merchant API and marketplace intelligence
- Firecrawl / site crawling
- Install scripts (`install.ps1`, `install.sh`)
- Python scripts, hooks, MCP extensions
- Live SERP fetching and competitor crawling

## Attribution

Rules adapted under MIT License. See [THIRD_PARTY_NOTICES.md](../../../../THIRD_PARTY_NOTICES.md) at repo root.
