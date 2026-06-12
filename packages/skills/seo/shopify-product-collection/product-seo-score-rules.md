# Product SEO Score Rules

## Componenti (0–100 ciascuno, pesati nel totale)

| Componente | Peso | Ottimo | Warning | Critico |
|------------|------|--------|---------|---------|
| score_title | 15 | Titolo chiaro ≥ 10 char | < 10 char | Assente |
| score_seo_title | 20 | Presente 30–60 char | < 30 o > 70 | Assente |
| score_meta_description | 20 | Presente 120–160 char | < 120 o > 170 | Assente |
| score_description | 15 | body ≥ 150 char testo | 50–149 | < 50 o assente |
| score_handle | 10 | handle leggibile kebab-case | corto/generico | assente |
| score_image_alt | 10 | tutte immagini con alt | parziale | nessun alt |
| score_tags | 10 | 1–10 tag coerenti | 0 tag | tag incoerenti |

## Severity da score_total

- **good**: ≥ 80
- **opportunity**: 60–79
- **warning**: 40–59
- **critical**: < 40

## Priorità business

Boost severity se:

- Best seller (top vendite) con score < 60 → minimo warning
- Stock > 0, zero vendite, score < 50 → opportunity alta

## Issues JSON structure

```json
{ "code": "missing_seo_title", "severity": "critical", "message": "...", "field": "seo_title" }
```
