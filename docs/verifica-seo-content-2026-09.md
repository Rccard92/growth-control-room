# Verifica pre-go-live — SEO Optimizer, Content Engine ed Editorial Shopify

**Data:** 2026-09-19
**Commit:** `023362c` + branch `claude/optimistic-euler-j17y8y`
**Perimetro:** sync prodotti/contenuti Shopify → analisi SEO → proposta (manuale/AI) → approvazione →
scrittura su Shopify; piano editoriale → brief → articolo → immagine → publish/schedule su Shopify.

Documento complementare a [`audit-2026-09.md`](audit-2026-09.md), che copre l'intero progetto.
Qui si risponde a una sola domanda: **questa parte funziona e si può mettere online?**

---

## Verdetto

**La pipeline è reale, completa e sostanzialmente corretta.** Non è una demo: la catena
sync → analisi → proposta → approvazione → apply funziona, scrive solo i campi effettivamente
cambiati, verifica i permessi Shopify in tempo reale prima di ogni scrittura e registra ogni
modifica. L'editorial arriva fino alla pubblicazione programmata con metafield SEO.

**Non è però pronta per andare online così com'è.** Ci sono 3 blocchi di configurazione e
sicurezza e 2 bug confermati che degradano silenziosamente l'output pubblicato.

Con le correzioni elencate in fondo, è materiale da produzione nel giro di pochi giorni di lavoro.

---

## Come ho verificato

| Verifica | Metodo | Esito |
|---|---|---|
| Test del modulo | `pytest -k "seo or editorial or content or shopify or metafield or apply or proposal"` | **481 test: 472 verdi, 9 rossi** |
| Natura dei 9 rossi | esecuzione singola e lettura del traceback | **tutti test stantii, nessun bug di prodotto** |
| Avvio reale dell'API | `uvicorn app.main:app` + probe HTTP | boot OK, `/health` e `/api/health` OK |
| Coerenza frontend ↔ backend | 142 path chiamati dal frontend vs 214 route dallo schema OpenAPI | **0 endpoint mancanti** |
| Catena score → diff → mutation | esecuzione diretta con dati realistici | corretta, vedi sotto |
| Sanitizer HTML articoli | test diretti su 9 casi | **2 bug confermati**, XSS invece solido |
| Mutation GraphQL vs API 2026-04 | documentazione Shopify | 2 mutation deprecate (funzionanti) |

---

## Cosa funziona davvero

### 1. Sync prodotti e contenuti

Paginazione cursor-based reale (`hasNextPage`/`endCursor`, 100 per pagina) su prodotti, varianti,
ordini, collections, pages, blogs, articles. I campi necessari allo scoring ci sono tutti:
`descriptionHtml`, `seo { title description }`, `handle`, `media { altText }`, `productType`,
metafield.

### 2. Analisi SEO

Scoring rule-based **trasparente e verificabile**, non una scatola nera AI. Prova eseguita su un
prodotto senza SEO title, senza meta description, descrizione corta e alt mancante:

```
score_total: 28 | severity: critical
componenti: title 100, seo_title 0, meta_description 0, description 20,
            handle 100, image_alt 0, tags 100
issues: missing_seo_title, missing_meta_description, weak_description, missing_image_alt
```

I pesi sommano a 100 e il breakdown per componente viene restituito all'UI. Le soglie
(SEO title 30-60, meta 120-160) sono esplicite in `seo_scoring_constants.py`.

### 3. Diff minimale prima della scrittura — il pezzo migliore

`compute_changed_proposed()` confronta proposta e valori correnti e manda a Shopify **solo il
delta**. Prova con una proposta che ripeteva titolo, descrizione e handle invariati e cambiava
solo SEO title, meta e un alt:

```
campi realmente cambiati: image_alts, media_images, meta_description, seo_title
input productUpdate: {"id": "gid://shopify/Product/9",
                      "seo": {"title": "...", "description": "..."}}
```

Titolo, descrizione e handle non compaiono nella mutation. È il comportamento giusto e riduce
di molto il rischio di danni collaterali sul negozio.

### 4. Controllo permessi prima di ogni scrittura

`can_apply_with_write_products()` non si fida della variabile d'ambiente: interroga Shopify
(`currentAppInstallation.accessScopes`, con fallback REST) a ogni apply e confronta gli scope
realmente concessi al token. Senza `write_products` l'apply si rifiuta con un messaggio che
distingue i due casi (scope non configurato vs token da riconnettere). Stesso schema per
`write_content` (publish) e `write_files` (immagini).

### 5. Dopo l'apply

Aggiornamento del record locale, rianalisi della singola entità, riga in `seo_change_logs` con
valori applicati e risposta Shopify completa. Se l'aggiornamento locale fallisce, la risposta lo
dichiara (`localUpdateFailed`) e suggerisce il sync manuale invece di mentire.

### 6. Editorial fino a Shopify

Piano editoriale → brief AI (approvazione richiesta) → articolo da brief approvato → immagine
hero generata, post-processata e caricata su Shopify Files (staged upload + `fileCreate`) →
`articleCreate`/`articleUpdate` con metafield SEO `global.title_tag` / `global.description_tag`.

Le protezioni presenti sono quelle giuste:
- **staleness guard**: se l'articolo è stato rigenerato dopo l'ultimo payload di pubblicazione,
  il publish si blocca con 409 invece di pubblicare contenuto vecchio;
- **conflitto di handle** rilevato con `find_article_by_handle` prima di creare un duplicato;
- **blog sempre risolto dentro lo store** del progetto (nessun rischio di scrivere sul blog sbagliato);
- **data programmata nel passato rifiutata** con errore esplicito (`schedule_in_past`);
- **SEO title e meta description obbligatorie** prima di pubblicare.

### 7. Sanitizer: solido sulla sicurezza

Testato direttamente:

```
<script>var x = "pericolo";</script>  → rimosso, contenuto incluso
<style>body{display:none}</style>     → rimosso
<p onclick="alert(1)">testo</p>       → <p>testo</p>
<a href="javascript:alert(1)">        → href rimosso
<a href="https://x.it" rel="nofollow">→ conservato
```

Nessuna via d'uscita XSS trovata.

### 8. Frontend allineato

Confronto automatico dei 142 path chiamati dal frontend contro le 214 route dello schema OpenAPI:
**nessuna chiamata verso endpoint inesistenti**. Non c'è drift tra front e back.

---

## Bug confermati

### 🔴 BUG 1 — Il sanitizer rompe la struttura dell'articolo pubblicato

**Dove:** `apps/api/app/utils/html_sanitize.py`, `_SanitizingHTMLParser.handle_endtag`

`<div>` è nella whitelist dei tag, ma solo con quattro classi consentite
(`gcr-article-body`, `gcr-article-note`, `gcr-product-tip`, `gcr-article-cta`). Un div con
qualsiasi altra classe viene scartato in apertura **senza essere messo sullo stack**. In chiusura,
però, `handle_endtag` vede `div` nella whitelist ed esegue un `while` che svuota lo stack finché
non trova un `div`: trova quello **esterno** e lo chiude.

**Riproduzione** (eseguita, pipeline reale sanitize → wrap):

```python
IN : <div class="gcr-article-body">
       <p>Intro.</p><h2>Sezione</h2><p>Testo.</p>
       <div class="faq"><h3>Domanda?</h3><p>Risposta.</p></div>
       <h2>Conclusione</h2><p>Finale.</p>
     </div>

OUT: <div class="gcr-article-body"><p>Intro.</p><h2>Sezione</h2><p>Testo.</p>
     <h3>Domanda?</h3><p>Risposta.</p></div><h2>Conclusione</h2><p>Finale.</p>
```

**Impatto:** il wrapper `gcr-article-body` si chiude a metà articolo. Tutto quello che segue
finisce **fuori** dal wrapper e perde il CSS del tema descritto in
[`shopify-article-theme-css.md`](shopify-article-theme-css.md). L'articolo va online con
tipografia e spaziature rotte dalla metà in poi. Nessun warning viene emesso.

È raggiungibile: basta che il modello generi un `<div>` con una classe non prevista (FAQ, box
ricetta, wrapper generico), cosa che le skill rules non impediscono tecnicamente. Vale anche per
le modifiche manuali fatte dall'editor in UI, che passano dallo stesso sanitizer.

**Fix:** in `handle_starttag`, quando un tag whitelisted viene scartato, marcarlo su uno stack di
"tag soppressi"; in `handle_endtag`, ignorare la chiusura se il tag non è effettivamente aperto,
invece di svuotare lo stack. Aggiungere un warning quando una classe div non consentita viene rimossa.

### 🔴 BUG 2 — Tabelle, a-capo e immagini inline vengono distrutti

Stesso file. `table`, `thead`, `tbody`, `tr`, `td`, `th`, `br`, `img`, `figure`, `h4`
non sono nella whitelist. Non vengono solo rimossi i tag: il contenuto collassa.

**Riproduzione** (eseguita):

```
IN : <h2>Ingredienti</h2><table><tr><td>Farina</td><td>200g</td></tr></table><p>Procedimento</p>
OUT: <h2>Ingredienti</h2>Farina200g<p>Procedimento</p>

IN : <p>Riga uno<br>Riga due</p><p><img src="..." alt="foto"></p>
OUT: <p>Riga unoRiga due</p><p></p>

IN : <h1>Titolo H1</h1><p>testo</p>
OUT: Titolo H1<p>testo</p>          (testo nudo, fuori da qualsiasi tag)
```

**Impatto:** per un brand che pubblica **ricette**, la tabella ingredienti è il formato naturale
e diventa `Farina200g`. Gli a-capo spariscono. Le immagini nel corpo articolo spariscono
silenziosamente (l'immagine hero passa da un percorso diverso e non è toccata).

**Fix:** allargare la whitelist a `table/thead/tbody/tr/th/td`, `br`, `figure/figcaption`, `h4`,
e `img` con `src` limitato al CDN Shopify e `alt` obbligatorio. Gestire i tag void
(`handle_startendtag`) che oggi non sono gestiti affatto.

### 🟠 BUG 3 — Il cambio di handle non crea il redirect

**Dove:** `apps/api/app/services/content/seo_apply_shopify.py`

`handle` è un campo proposto dall'AI (`seo_proposal_field_engine.py` ha un prompt dedicato:
*"Genera solo un handle URL SEO-friendly"*), è modificabile in UI (`SeoFieldEditor.tsx`, campo
"Handle URL") e viene scritto in `ProductInput.handle` / `CollectionInput.handle`.

`redirectNewHandle` **non è mai impostato** — la stringa non compare da nessuna parte nel
codebase. La documentazione Shopify descrive quel campo come *"Whether a redirect is required
after a new handle has been provided. If true, then the old handle is redirected to the new one
automatically"*, quindi omettendolo il redirect non viene creato.

**Impatto:** cambiare l'handle di un prodotto posizionato significa 404 sul vecchio URL, perdita
del ranking e dei backlink. Su uno strumento il cui scopo è **migliorare** la SEO, è il danno
peggiore possibile, ed è silenzioso.

**Fix:** impostare `redirectNewHandle: true` ogni volta che `handle` è nel delta. In UI, marcare
il campo handle come azione ad alto impatto con conferma dedicata. Da verificare sullo store di
test prima del go-live, perché è il punto più costoso da sbagliare.

### 🟡 BUG 4 — `/api/debug/routes` è rotto (e dimostra un rischio più grosso)

Verificato sull'API avviata: l'endpoint risponde `{"count": 5, ...}` invece delle 214 route reali.

FastAPI 0.141 non appiattisce più le route incluse in `app.routes`: al loro posto mette oggetti
`_IncludedRouter`, che il filtro `isinstance(route, Route)` scarta. Il codice è stato scritto
contro una versione precedente.

Non è grave di per sé — ma è la **prova concreta** del rischio già segnalato nell'audit: le
dipendenze non sono bloccate (`fastapi>=0.115`, `uv.lock` in `.gitignore`) e il `Dockerfile.api`
risolve tutto da zero a ogni build. Una funzione si è già rotta da sola, senza che nessuno
toccasse il codice. Può succedere a qualcosa di più importante.

### 🟡 BUG 5 — I 9 test rossi sono tutti stantii (nessun bug di prodotto)

Verificati uno per uno:

| Test | Causa | Tipo |
|---|---|---|
| `test_editorial_schedule_utils` (2) | data hardcoded `2026-07-05`, oggi passata | scadenza |
| `test_editorial_shopify_publish` (1) | idem — la guardia "data futura" funziona correttamente | scadenza |
| `test_editorial_publishing_read` (3) | fake `SimpleNamespace` senza `image_payload` | doppio stantio |
| `test_editorial_article_service` (1) | idem | doppio stantio |
| `test_editorial_ai_usage` (1) | mock esaurito: il codice fa più query di quante ne prevede il test | doppio stantio |
| `test_editorial_item_reschedule` (1) | `reschedule` ora legge lo store per il fuso orario; il test asserisce `execute` mai chiamato | doppio stantio |

**Nessuno indica un difetto del prodotto.** Ma i 4 su `image_payload` falliscono da quando è
stata aggiunta la migration `035_editorial_image_payload` e nessuno se n'è accorto: senza CI, la
suite non protegge nulla.

---

## Blocchi al go-live

### ⛔ 1. Gli endpoint di scrittura su Shopify sono pubblici e senza autenticazione

Questo modulo espone, **senza alcun controllo di accesso**:

```
POST .../content/seo/proposals/{id}/apply          → scrive su prodotti/collection
POST .../content/seo/entities/apply-fields         → scrive su prodotti/collection
POST .../content/seo/editorial-items/{id}/publish-shopify → pubblica sul blog
POST .../content/seo/proposals/generate            → spesa OpenAI
POST .../content/seo/editorial-items/{id}/generate-article → spesa OpenAI
POST .../shopify/sync                              → sync completo
```

Chiunque conosca l'URL dell'API e un `project_id` può modificare le schede prodotto o pubblicare
articoli sul negozio del cliente. **Non si può mettere online prima di aver risolto questo.**

### ⛔ 2. `write_products` manca dagli scope di default → l'apply non funziona appena installato

`SHOPIFY_SCOPES` vale, sia in `config.py` sia in `.env.example` sia nel README:

```
read_products,read_orders,read_content,write_content,read_reports,read_files,write_files
```

`write_products` **non c'è**, ma è esattamente lo scope che `REQUIRED_FOR_APPLY` pretende. Con la
configurazione documentata, ogni apply risponde *"write_products non è configurato in
SHOPIFY_SCOPES"*. Il sistema degrada in modo pulito e il messaggio è corretto, ma la funzione
principale del modulo è spenta.

**Fix:** aggiungere `write_products` a `SHOPIFY_SCOPES` (config, `.env.example`, README, app
Shopify) e **riconnettere** lo store: i token esistenti non ereditano i nuovi permessi.

### ⛔ 3. Il sync gira dentro la richiesta HTTP, senza throttling

`POST /api/projects/{id}/shopify/sync` esegue `sync_shopify_store()` in modo sincrono: scarica
**tutti** i prodotti in una lista Python, poi tutti gli ordini, poi ricostruisce le metriche, e
solo alla fine risponde.

Tre conseguenze su un catalogo vero:
- **timeout del gateway** su store grandi, senza possibilità di riprendere;
- **memoria**: l'intero catalogo con `descriptionHtml`, media e metafield sta in RAM;
- **nessuna gestione di `THROTTLED`**: `execute_raw` tratta 401/403/4xx ma non l'errore di
  throttling GraphQL né `Retry-After` né il `throttleStatus` nelle `extensions`.

Su un catalogo piccolo (qualche centinaio di prodotti) passa. Su migliaia, si rompe.

**Fix minimo per il go-live:** spostare il sync su un job in background con stato leggibile
dall'UI, e aggiungere retry con backoff sull'errore THROTTLED. È lo stesso job runner previsto
in Fase 1 della roadmap — qui serve una versione ridotta.

---

## Rischi medi (non bloccanti, da mettere subito a backlog)

| # | Problema | Impatto |
|---|---|---|
| 1 | **Nessuna guardia di concorrenza sull'apply prodotti.** Il delta è calcolato su `current_values` congelati al momento della proposta. Se nel frattempo qualcuno modifica il prodotto in Shopify, GCR sovrascrive senza avvisare. L'editorial ha la staleness guard, il SEO Optimizer no. | Sovrascrittura silenziosa del lavoro altrui |
| 2 | **Apply non atomico.** Se l'update scalare riesce e l'update degli alt fallisce, la risposta dice `applied: false` e la proposta resta `approved`, ma su Shopify il primo pezzo è già stato scritto. | Stato incoerente, messaggio fuorviante |
| 3 | **Mutation deprecate.** `productUpdate(input: ProductInput!)` è deprecata dal 2025-04 a favore di `productUpdate(product: ProductUpdateInput!)`; `productUpdateMedia` è deprecata a favore di `fileUpdate`. Entrambe risultano ancora documentate nelle versioni 2026, quindi **oggi funzionano**. | Rottura futura a scadenza ignota |
| 4 | **N+1 nell'analisi.** `analyze_products_for_store` esegue una `SELECT` di `SeoEntityAnalysis` per ogni prodotto. 5.000 prodotti = 5.000 query. | Analisi lenta, carico DB |
| 5 | **Solo i prodotti `ACTIVE` vengono analizzati**, gli altri sono saltati in silenzio e non compaiono in nessun conteggio. | L'utente non sa perché mancano |
| 6 | **Nessuna validazione di lunghezza in scrittura.** Le soglie 30-60 / 120-160 valgono solo per lo score: un meta da 400 caratteri viene scritto su Shopify comunque. | Il tool può scrivere SEO che il suo stesso scorer boccia |
| 7 | **Costo immagini non tracciato** per `gpt-image-2`: non è in `IMAGE_MODEL_PRICING_USD` e il match parziale non lo intercetta, quindi la stima torna `None`. | Le immagini non pesano sui budget guardrail |
| 8 | **Un nuovo `httpx.AsyncClient` per ogni chiamata Shopify**, nessun connection pooling. | Latenza extra sui sync |
| 9 | `target="_blank"` viene rimosso dai link degli articoli. | I link esterni aprono nella stessa scheda |

---

## Checklist pre-go-live

### Minima — senza questi non si va online

- [ ] **Autenticazione** su tutti gli endpoint del modulo, con test che fallisce se un endpoint resta scoperto
- [ ] **Cifratura reale dei token** (Fernet) + rotazione dei token Shopify già emessi
- [ ] **`write_products`** aggiunto a `SHOPIFY_SCOPES` e store riconnesso
- [ ] **`redirectNewHandle: true`** quando l'handle cambia — verificato sullo store di test
- [ ] **BUG 1 e BUG 2** del sanitizer corretti, con test di regressione
- [ ] **`CORS_ORIGINS`** ristretto al dominio WEB, senza default `*`
- [ ] **`uv.lock` committato** e dipendenze bloccate
- [ ] **`/api/debug/routes`** rimosso o protetto

### Consigliata — prima di dare il tool in mano a un cliente

- [ ] Sync spostato su job in background con stato in UI
- [ ] Retry con backoff su `THROTTLED` Shopify
- [ ] Guardia di concorrenza sull'apply: rilettura dei valori live prima di scrivere, 409 se divergono
- [ ] 9 test stantii sistemati (`freezegun` + fake aggiornati) e **CI attiva**
- [ ] Validazione di lunghezza SEO title / meta prima della scrittura
- [ ] N+1 dell'analisi risolto con un fetch unico
- [ ] Prova end-to-end su uno **store di sviluppo** con dati reali: sync completo → analisi →
      proposta AI → apply → verifica in Shopify Admin → articolo generato → publish programmato →
      verifica del rendering sul tema

### Collaudo su store di test — l'unica prova che conta

Niente di quanto sopra sostituisce una passata completa su uno store Shopify di sviluppo. Le
verifiche di questo documento sono statiche e di unit test: **nessuna chiamata reale a Shopify è
stata eseguita**, perché richiede credenziali di uno store vero. I punti da osservare in quella
passata sono, in ordine: apply di un campo scalare, apply di un alt immagine, cambio di handle
(con verifica del redirect), pubblicazione di un articolo con tabella e box, e il rendering finale
sul tema.
