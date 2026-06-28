---
name: gcr-editorial-article
version: "v1"
description: >
  Growth Control Room editorial article skill pack.
  Readability, neuromarketing, Shopify HTML formatting and structure rules for blog articles.
---

# GCR Editorial Article Skill

## Nome

GCR Editorial Article Skill (`gcr-editorial-article`)

## Obiettivo

Generare articoli blog Shopify leggibili, scansionabili, SEO-oriented e orientati alla conversione — non documenti Word lunghi e piatti.

## Input

- Tipo contenuto editoriale (educational, recipe, product_guide, FAQ, storytelling, …)
- Brief SEO approvato (struttura H2/H3, keyword, claim, CTA)
- Brand Intelligence (tono, Safe Claims, editorial guidelines)
- Prodotto/collezione collegata (handle/URL se disponibili)

## Output

- Brief con checklist editoriale, piano link interni, box HTML suggeriti
- Articolo con `bodyHtml` formattato (H2/H3, liste, grassetti, box GCR, FAQ brevi, CTA)
- Checklist qualità e warnings non bloccanti

## Priorità

1. **Safe Claims** — priorità assoluta su tutte le regole
2. Leggibilità e scanability
3. Struttura proporzionata al tipo contenuto
4. Neuromarketing etico (fiducia, non manipolazione)
5. SEO naturale — non allungare solo per keyword

## File regole

- `article-structure-rules.md` — limiti per tipo contenuto
- `readability-rules.md` — paragrafi, liste, box, grassetti
- `neuromarketing-rules.md` — angolo emotivo etico
- `shopify-html-rules.md` — tag HTML e classi GCR
- `internal-linking-rules.md` — link reali vs suggerimenti
- `faq-format-rules.md` — FAQ brevi e visive
- `source-map.md` — tracciabilità origine regole
