# Brand Intelligence

Brand Intelligence è la knowledge base del brand in Growth Control Room. **v0.3.2** estende Brand Identity con import scoped da singolo file e contesto machine-ready per i moduli AI.

## Strategia v0.3.2 — Identity import + context machine-ready

La UI espone quattro tab:

1. **Overview** — tre card di stato (Profile, Identity, Visual Identity)
2. **Brand Profile** — fonti URL, proposta AI, profilo ufficiale
3. **Brand Identity** — form manuale + **import da 1 file** (PDF/DOCX/TXT/MD) con proposta AI
4. **Visual Identity** — logo, palette, font + estrazione da sito

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
- **promptContext**: testo pulito per moduli AI (`brandProfile`, `brandIdentity`, `visualIdentity`, `fullText`)

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
