# Ottimizzazione costi AI

Guida rapida per ridurre i costi OpenAI senza degradare la qualità dei contenuti strategici.

## Principi

1. **Context Profiles** — invia solo i blocchi brand necessari per il task (`context_profiles.py`).
2. **Model Routing** — usa il tier minimo adeguato per ogni profilo (`model_policy.py`).
3. **Usage Monitor** — controlla costo, token e tier nella pagina **AI Costs**.
4. **Prompt cache key** — prefix stabile per favorire cache provider dove supportata.

## Task → context profile → model tier

| Task | Context profile | Tier | Max output tokens |
|------|-----------------|------|-------------------|
| Alt immagine prodotto | `image_alt` | cheap | 120 |
| Meta title/description singolo campo | `product_seo_field` / `collection_seo_field` | cheap | 400 |
| Task BI minimi | `minimal` | cheap | 500 |
| Risposta social | `social_response` | cheap | 600 |
| Proposta SEO completa | `product_seo_full` / `collection_seo_full` | standard | 2500 |
| Brief editoriale | `blog_brief` | standard | 3000 |
| Import/sintesi Brand Intelligence | `brand_import` | standard | 4500 |
| Compliance review | `compliance_review` | standard* | 1500 |
| Fallback generico | `generic` | standard | 2000 |
| Articolo da brief | `article_draft` | premium | 8000 |

\* Se `OPENAI_MODEL_REASONING` è configurato, `compliance_review` usa tier `reasoning`; altrimenti `standard`. Mai `cheap`.

## Variabili env consigliate

| Env | Ruolo |
|-----|-------|
| `OPENAI_MODEL` | Fallback legacy finale (non modello operativo primario) |
| `OPENAI_MODEL_CHEAP` | Tier cheap (default: `OPENAI_MODEL`) |
| `OPENAI_MODEL_STANDARD` | Tier standard (default: `OPENAI_MODEL`) |
| `OPENAI_MODEL_PREMIUM` | Tier premium (default: `gpt-4o`) |
| `OPENAI_MODEL_REASONING` | Modello reasoning opzionale |
| `OPENAI_MODEL_FALLBACK` | Ripiego se tier non risolvibile |
| `AI_DAILY_BUDGET_USD` / `AI_MONTHLY_BUDGET_USD` | Guardrail budget |
| `AI_ENABLE_MODEL_FALLBACK_ON_SCHEMA_ERROR` | Retry standard su errori JSON |

## Come cambiare modello da UI

1. Apri **AI Costs** nel progetto
2. Tab **Model Settings**
3. Trova il punto AI (es. `product_image_alt`)
4. Clic **Modifica** → scegli modello (select o input libero), tier, max tokens, temperature
5. **Salva** — la prossima generazione usa il nuovo modello senza redeploy Railway
6. **Ripristina** torna al consigliato registry/env

Banner in pagina: le variabili Railway sono solo default/fallback — **non** sostituiscono le impostazioni salvate in Model Settings.

## Ordine risoluzione modello

1. Impostazione progetto da UI (`ai_model_settings`, `source=manual`)
2. Impostazione globale (`project_id` NULL)
3. Registry default + env tier (seed iniziale)
4. `OPENAI_MODEL_CHEAP` / `STANDARD` / `PREMIUM` / `REASONING` / `FALLBACK`
5. `OPENAI_MODEL` legacy — solo fallback finale

`OPENAI_MODEL` non va rimosso da Railway, ma non comanda le richieste se esistono setting specifici per operation.

## Verifica in AI Costs

1. Filtra per **tier** `cheap` — alt e campi singoli devono comparire qui.
2. Brief e proposte SEO complete → tier `standard`.
3. Articoli → tier `premium`.
4. Controlla **Model Routing Insights** per:
   - costo/richieste per tier
   - warning premium su profili cheap
   - retry schema fallback
   - tier senza modello env configurato

## Roadmap

- Caching risposte per hash prompt + profilo
- Stima pre-run costo per operazione batch
- Dashboard workspace con aggregazione multi-progetto
