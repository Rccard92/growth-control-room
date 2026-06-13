# Brand Intelligence

Brand Intelligence è la knowledge base del brand in Growth Control Room. **v0.3.4** aggiunge Product Knowledge modulare: regole generali + schede prodotto collegate a Shopify.

## Strategia v0.3.4 — Product Knowledge

La UI espone sei tab:

1. **Overview** — sei card di stato (Profile, Identity, Visual, Safe Claims, Product Knowledge)
2. **Brand Profile** — fonti URL, proposta AI, profilo ufficiale
3. **Brand Identity** — form manuale + import da 1 file
4. **Visual Identity** — logo, palette, font + estrazione da sito
5. **Safe Claims & Red Flags** — claim consentiti/vietati, red flags
6. **Product Knowledge** — regole generali + schede prodotto Shopify

### Due livelli

| Livello | Tabella | Uso |
|---------|---------|-----|
| **Generale** | `brand_product_knowledge_general` | Principi validi per tutti i prodotti |
| **Specifico** | `brand_product_knowledge_items` | Scheda per prodotto Shopify (FK `shopify_products`) |

### Import file (solo generale)

1. Carica **un solo file** (catalogo, scheda tecnica, linee guida)
2. L'AI estrae **solo** regole generali; dettagli di singoli prodotti (es. "Miele di Limone") → principi comuni, **non** schede specifiche
3. Applica proposta → `brand_product_knowledge_general`
4. Nessun auto-save

### Schede prodotto da Shopify

1. CTA "Aggiungi prodotto da Shopify" → lista prodotti sincronizzati
2. `POST .../items/from-shopify` crea scheda precompilata (nome, handle, GID, product line)
3. Compilazione manuale accordion; salvataggio per item
4. Import file per singolo prodotto: **non in v1**

**Completion modulo:** generale presente **e** ≥1 item = completo; generale **oppure** ≥1 item = parziale.

**Legacy:** `brand_product_knowledge` + route `.../products` restano deprecati.

### Endpoint Product Knowledge (v0.3.4)

| Metodo | Path |
|--------|------|
| GET/PUT | `/brand-intelligence/product-knowledge/general` |
| POST | `/brand-intelligence/product-knowledge/general/import-file` |
| POST | `/brand-intelligence/product-knowledge/general/apply-proposal` |
| GET | `/brand-intelligence/product-knowledge/shopify-products` |
| GET/POST | `/brand-intelligence/product-knowledge/items` |
| POST | `/brand-intelligence/product-knowledge/items/from-shopify` |
| GET/PUT/DELETE | `/brand-intelligence/product-knowledge/items/{item_id}` |

### Context machine-ready

`GET /context` espone `productKnowledge.generalRules` + `productKnowledge.specificProducts[]`.
`promptContext.productKnowledge` include blocchi `PRODUCT KNOWLEDGE — GENERAL` e `SPECIFIC PRODUCTS`.
Product SEO: lookup per `shopify_product_id` + fallback solo generale se item assente.

---

## Strategia v0.3.3 — Safe Claims & Red Flags

La UI (v0.3.3) ha introdotto Safe Claims come quarto modulo.

### Flusso Safe Claims da file

1. L'utente carica **un solo file** (policy, legal, brand guidelines)
2. L'AI estrae **solo** Safe Claims (allowed/forbidden/caution, disclaimer, red flags)
3. L'utente modifica la proposta in UI
4. **Applica proposta** → scrittura ufficiale su `brand_safe_claims`
5. Il form manuale si aggiorna e resta editabile

**Completion:** almeno 1 claim consentito + 1 vietato + (1 cautela **oppure** 1 disclaimer).

**Legacy:** `brand_claim_rules` / CRUD `.../claims` resta deprecato e non usato dal nuovo flusso.

### Endpoint Safe Claims (v0.3.3)

| Metodo | Path | Ruolo |
|--------|------|-------|
| GET/PUT | `/brand-intelligence/safe-claims` | Safe Claims manuale |
| POST | `/brand-intelligence/safe-claims/import-file` | Estrazione testo + proposta AI (preview) |
| POST | `/brand-intelligence/safe-claims/apply-proposal` | Applica proposta dopo conferma |

### Ruolo nei moduli AI

- `BrandContextBuilder` include blocco `SAFE CLAIMS & RED FLAGS` in `promptContext.fullText`
- Se Safe Claims vuota → fallback statico di prudenza + voce in `missingContext`
- Product SEO e Content SEO usano `get_prompt_context()` senza modifiche alle chiamate esistenti

---

## Strategia v0.3.2 — Identity import + context machine-ready

La UI (v0.3.2) ha introdotto import Identity e `promptContext` machine-ready.

### Flusso Brand Identity da file

```mermaid
flowchart LR
  File[1 file PDF/DOCX/TXT/MD] --> Import[POST identity/import-file]
  Import --> Preview[Proposta AI in memoria]
  Preview --> Review[Utente revisiona]
  Review --> Apply[POST identity/apply-proposal]
  Apply --> Official[(brand_identities ufficiale)]
  Official --> CTX[BrandContextBuilder]
```

1. L'utente carica **un solo file** dedicato all'identità del brand
2. L'AI estrae **solo** campi Brand Identity (posizionamento, valori, principi, storytelling)
3. L'utente modifica la proposta in UI
4. **Applica proposta** → scrittura ufficiale su `brand_identities`
5. Il form manuale si aggiorna e resta editabile

**Non include:** batch import, extracted facts, section drafts, brief, Product Knowledge, FAQ, Claims, PED.

### Endpoint attivi (v0.3.2)

| Metodo | Path | Ruolo |
|--------|------|-------|
| GET/PUT | `/brand-intelligence/identity` | Brand Identity manuale |
| POST | `/brand-intelligence/identity/import-file` | Estrazione testo + proposta AI (preview) |
| POST | `/brand-intelligence/identity/apply-proposal` | Applica proposta dopo conferma |
| GET/PUT | `/brand-intelligence/profile` | Brand Profile |
| GET/PUT | `/brand-intelligence/visual-identity` | Visual Identity |
| POST | `/brand-intelligence/visual-identity/extract-from-website` | Estrazione visuale |
| POST | `/brand-intelligence/visual-identity/apply-proposal` | Applica proposta visuale |
| GET | `/brand-intelligence/context` | Bundle machine-ready + `promptContext` |

### Context machine-ready vs UI human-friendly

- **UI**: form editabili, proposte AI, liste multilinea — pensati per revisione umana
- **Context API** (`GET /context`): JSON strutturato con `brandContextVersion: v1`, `brandProfile`, `brandIdentity`, `visualIdentity`, `missingContext`
- **promptContext**: testo pulito per moduli AI (`brandProfile`, `brandIdentity`, `visualIdentity`, `safeClaims`, `fullText`)

I moduli AI (Content SEO, Product SEO, futuri PED/Ads/Email) devono usare `BrandContextBuilder.get_prompt_context()` — non i campi UI raw.

### Regola fondamentale

**Nessun salvataggio automatico dati AI.** Import-file e enrich generano solo preview; solo `PUT` o `apply-proposal` scrivono i dati ufficiali.

---

## Endpoint deprecati (non usati da UI v1)

Restano nel backend per compatibilità DB/migration, marcati `deprecated` in OpenAPI:

- Import AI batch, extracted facts, section drafts, brief mode
- CRUD sezioni avanzate legacy

### Test manuali

1. Brand Identity → carica PDF → Genera proposta → Applica → refresh → dati persistiti
2. `GET .../context` → `brandIdentity` + `promptContext.fullText` pulito
3. File non supportato / vuoto → errore leggibile
4. OPENAI_API_KEY assente → errore 503 leggibile
