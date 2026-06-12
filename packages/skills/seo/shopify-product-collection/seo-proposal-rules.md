# SEO Proposal Rules

## Product proposal JSON

```json
{
  "proposed_product_title": "...",
  "proposed_seo_title": "...",
  "proposed_meta_description": "...",
  "proposed_handle": "...",
  "proposed_tags": [],
  "proposed_image_alts": [{ "media_id": "...", "proposed_alt": "..." }],
  "reasoning": ["..."],
  "risk_level": "low|medium|high"
}
```

## Collection proposal JSON

```json
{
  "proposed_collection_title": "...",
  "proposed_seo_title": "...",
  "proposed_meta_description": "...",
  "proposed_description": "...",
  "proposed_handle": "...",
  "proposed_image_alt": "...",
  "reasoning": ["..."],
  "risk_level": "low|medium|high"
}
```

## Risk levels

- **low**: solo meta/alt mancanti, nessun cambio title/handle
- **medium**: modifica title o description
- **high**: modifica handle o claim sensibili

## Source

- `ai`: OpenAI con skill rules
- `rules`: fallback conservativo (solo campi vuoti)
