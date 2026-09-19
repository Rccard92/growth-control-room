# Growth Control Room

Piattaforma multi-brand per monitorare progetti e-commerce e marketing.

Ogni utente può creare più progetti. Ogni progetto può collegare integrazioni diverse: Shopify, Meta Ads, Google Ads, Klaviyo, Google Search Console, GA4, Merchant Center e TikTok Ads.

## Struttura monorepo

```
growth-control-room/
├── apps/
│   ├── web/          # Frontend React + Vite + TypeScript
│   └── api/          # Backend Python FastAPI
├── packages/
│   ├── shared/       # Tipi e costanti TypeScript condivisi
│   ├── ui/           # Componenti React condivisi
│   ├── connectors/   # Connettori integrazioni (Python)
│   └── skills/       # Skill AI (Python)
└── docs/             # Documentazione
```

## Prerequisiti

- [Node.js](https://nodejs.org/) 20+
- [pnpm](https://pnpm.io/) 9+
- [uv](https://docs.astral.sh/uv/) (gestore Python)
- [Docker](https://www.docker.com/) e Docker Compose

## Quick start

### 1. Avvia PostgreSQL

```bash
pnpm db:up
```

### 2. Installa dipendenze JavaScript

```bash
pnpm install
```

Se `pnpm` non è disponibile: `corepack enable` oppure `npx pnpm install`.
Con pnpm 10+, al primo install potrebbe servire: `pnpm approve-builds esbuild`.

### 3. Installa dipendenze Python

```bash
uv sync
```

Su Windows, se `uv` non è nel PATH: `python -m pip install uv` poi `python -m uv sync --all-packages`.
Se compaiono errori TLS: aggiungi `--system-certs`.

### 4. Esegui le migration

```bash
pnpm db:migrate
```

Crea lo schema foundation e il seed demo (User `admin@growthcontrolroom.local`, Workspace `Growth Control Room`).

### 5. Avvia backend e frontend

Copia `.env.example` in `.env` e imposta `VITE_API_URL=http://localhost:8000` per collegare il frontend all'API in locale.

```bash
pnpm dev
```

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Health check: http://localhost:8000/api/health
- Progetti: http://localhost:8000/api/projects

### Avvio singolo

```bash
pnpm dev:web   # solo frontend
pnpm dev:api   # solo backend
```

## Variabili d'ambiente

Copia `.env.example` in `.env` e adatta i valori se necessario.

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `VITE_API_URL` | *(vuoto)* | URL base API per il frontend (build-time su Railway) |
| `DATABASE_URL` | *(obbligatoria)* | Connessione PostgreSQL; in locale con `APP_ENV=development` usa il default da `.env` |
| `SECRETS_ENCRYPTION_KEY` | *(obbligatoria in produzione)* | Chiave Fernet per cifrare i token di integrazione |
| `CORS_ORIGINS` | *(obbligatoria in produzione)* | Origini consentite, separate da virgola. `*` è rifiutato fuori da `development` |
| `APP_ENV` | `production` | Ambiente applicazione (`development` in locale) |
| `INITIAL_ADMIN_EMAIL` | *(vuoto)* | Email del primo account amministratore |
| `INITIAL_ADMIN_PASSWORD` | *(vuoto)* | Password del primo account (min. 12 caratteri) |

### Autenticazione

L'API richiede un account per tutti gli endpoint tranne health, login e le callback OAuth
dei provider. Al primo avvio, se `INITIAL_ADMIN_EMAIL` e `INITIAL_ADMIN_PASSWORD` sono
impostate e non esiste ancora un utente con password, viene creato l'account amministratore
e collegato al workspace. Agli avvii successivi non viene toccato nulla.

Genera la chiave di cifratura con:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Per ruotarla: metti la nuova chiave **per prima** in `SECRETS_ENCRYPTION_KEY` (separata da
virgola dalla vecchia), redeploy, poi riscrivi le credenziali e togli la vecchia chiave.

## Deploy su Railway

Due servizi separati: **API** (FastAPI) e **WEB** (Vite preview).

### Servizio API

| Variabile | Esempio |
|-----------|---------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (**obbligatoria** sul servizio API) |
| `SECRETS_ENCRYPTION_KEY` | chiave Fernet (**obbligatoria**) |
| `CORS_ORIGINS` | `https://web-xxx.up.railway.app` (**obbligatoria**, niente `*`) |
| `APP_ENV` | `production` |
| `INITIAL_ADMIN_EMAIL` | `tu@dominio.it` |
| `INITIAL_ADMIN_PASSWORD` | password di almeno 12 caratteri |

`DATABASE_URL` deve essere impostata sul servizio **API**, non solo sul database Postgres. Senza questa variabile il container fallisce all'avvio con un errore esplicito. Railway fornisce spesso `postgresql://` o `postgres://`; la config converte automaticamente per asyncpg (FastAPI) e psycopg (Alembic).

Anche `SECRETS_ENCRYPTION_KEY` e `CORS_ORIGINS` sono obbligatorie sul servizio API in
produzione: senza, il container si rifiuta di partire con un messaggio esplicito.

**Migration.** Il container non esegue più `alembic upgrade head` all'avvio: con più di
una replica le migration si sovrapporrebbero sullo stesso database. Esegui `./scripts/migrate.sh`
come release step (o una tantum da console) prima di promuovere la nuova versione.

### Servizio WEB

| Variabile | Esempio |
|-----------|---------|
| `VITE_API_URL` | `https://api-xxx.up.railway.app` (senza `/api` finale) |
| `PORT` | *(impostata da Railway)* porta su cui ascolta nginx |

Il servizio WEB serve la build statica con **nginx** (compressione, header di cache e di
sicurezza). `vite preview` era un server di sviluppo e non è più usato in produzione.

`VITE_API_URL` è una variabile di **build**: imposta l'URL base dell'API **senza** suffisso `/api` (es. `https://api-xxx.up.railway.app`, non `.../api`). Il frontend aggiunge automaticamente i path `/api/projects`, ecc. Rebuild obbligatorio dopo ogni modifica.

Lascia vuoto lo Start Command su entrambi i servizi (usa il CMD del Dockerfile).

### Post-deploy

1. Imposta `SECRETS_ENCRYPTION_KEY`, `CORS_ORIGINS` e le credenziali admin sul servizio API
2. Esegui le migration (`./scripts/migrate.sh`): la `044` ricifra i token salvati in
   precedenza, la `045` crea le tabelle di autenticazione
3. Redeploy API, poi accedi con l'account amministratore
4. Redeploy WEB con `VITE_API_URL` impostato all'URL pubblico dell'API
5. **Riconnetti Shopify e Google**: i token erano salvati senza cifratura reale, quindi
   vanno considerati compromessi e riemessi. La riconnessione serve anche per ottenere
   `write_products`.

## Integrazione Shopify (OAuth)

Connessione store tramite OAuth Shopify. L'utente inserisce solo il dominio shop e autorizza l'app su Shopify Admin.

### Creare l'app Shopify (Partner / Dev Dashboard)

1. Crea un'app su [Shopify Partners](https://partners.shopify.com) o dal Dev Dashboard dello store
2. **App URL**: `https://web-production-77355.up.railway.app`
3. **Allowed redirection URL(s)**:
   `https://api-production-1077.up.railway.app/api/integrations/shopify/oauth/callback`
4. Configura gli **Admin API scopes**:
   - `read_products`
   - `write_products` (apply proposte SEO su prodotti e collection)
   - `read_orders`
   - `read_content`
   - `write_content` (pubblicazione articoli blog)
   - `read_reports` (ShopifyQL / Analytics ufficiali)
   - `read_files`, `write_files` (immagini hero editoriali su Shopify Files)
5. Copia **Client ID** e **Client secret** dall'app

### Variabili Railway (servizio API)

| Variabile | Valore esempio |
|-----------|----------------|
| `SHOPIFY_CLIENT_ID` | da Shopify App settings |
| `SHOPIFY_CLIENT_SECRET` | da Shopify App settings |
| `SHOPIFY_SCOPES` | `read_products,write_products,read_orders,read_content,write_content,read_reports,read_files,write_files` |
| `SHOPIFY_REDIRECT_URI` | `https://api-production-1077.up.railway.app/api/integrations/shopify/oauth/callback` |
| `FRONTEND_URL` | `https://web-production-77355.up.railway.app` |

Assicurati che `CORS_ORIGINS` includa il dominio WEB.

Dopo ogni modifica agli scope serve **riconnettere Shopify**: i token OAuth gia'
emessi non ereditano i nuovi permessi. Verifica con
`GET /api/projects/{id}/shopify/scopes`.

### Sync automatico

Il sync Shopify non è più solo manuale. L'API esegue un ciclo periodico che
risincronizza gli store collegati i cui dati sono più vecchi della soglia configurata.
Il ciclo prende un **advisory lock Postgres**, quindi con più repliche ne lavora una sola.

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `SHOPIFY_AUTO_SYNC_ENABLED` | `true` | Abilita il ciclo automatico |
| `SHOPIFY_AUTO_SYNC_INTERVAL_MINUTES` | `180` | Ogni quanto controllare gli store |
| `SHOPIFY_AUTO_SYNC_MAX_AGE_MINUTES` | `720` | Età oltre la quale uno store va risincronizzato |

Con i default, ogni store viene aggiornato almeno due volte al giorno.

**Limite Shopify da conoscere:** con lo scope `read_orders` (senza `read_all_orders`,
che richiede approvazione Partner) l'API espone solo gli **ultimi 60 giorni** di ordini.
Se il sync resta fermo più a lungo, gli ordini nel mezzo non sono più recuperabili.

### Copertura dati nella dashboard

Le metriche ordine sono calcolate su quello che il sync ha in locale. Se il periodo
selezionato non è coperto dall'ultimo sync, la dashboard mostra `n/d` al posto di `0,00 €`
e un banner che spiega il motivo, invece di far sembrare "nessuna vendita" quello che in
realtà è "nessun dato". Il campo `orderDataCoverage` della risposta espone
`status` (`covered` / `partial` / `uncovered` / `never_synced`) e `orderMetricsReliable`.

### Flusso utente

1. Apri un progetto → **Integrazioni** → Shopify → **Connetti**
2. Inserisci il dominio shop (`nomesito.myshopify.com` o solo `nomesito`)
3. Clicca **Connetti Shopify** → redirect su Shopify Admin
4. Autorizza Growth Control Room → ritorno automatico alla piattaforma
5. Usa **Sincronizza dati** per importare prodotti e ordini

### Endpoint API Shopify

- `GET /api/projects/{id}/integrations/shopify/oauth/start?shop=...`
- `GET /api/integrations/shopify/oauth/callback` (redirect Shopify)
- `POST /api/projects/{id}/integrations/shopify/connect` (solo connessione manuale avanzata)
- `GET /api/projects/{id}/shopify/status`
- `POST /api/projects/{id}/shopify/sync`
- `GET /api/projects/{id}/shopify/dashboard`

## Documentazione

- [Architettura](docs/architecture.md)
- [Brand Intelligence](docs/brand-intelligence.md)
- [Architettura AI](docs/ai-architecture.md)
- [Integrazioni](docs/integrations.md)

## Brand Intelligence

Ogni progetto può definire un profilo brand strutturato (voice, prodotti, audience, claims, SEO, guardrails) con **Brand Knowledge Score**, wizard guidato e **Import AI** da documenti.

**Onboarding:** compilazione manuale minima oppure upload file con estrazione AI e review umana prima del salvataggio.

**Regola architetturale:** i moduli AI che generano contenuti brand-facing devono chiamare `BrandIntelligenceContextBuilder.build_brand_context(project_id)`. Le estrazioni AI sono suggestions in `brand_extracted_facts` — solo i facts approvati e applicati entrano nel contesto ufficiale.

Vedi [docs/brand-intelligence.md](docs/brand-intelligence.md) e [docs/ai-architecture.md](docs/ai-architecture.md).

## Stato attuale

Implementato:

- **Frontend Foundation v1**: UI dark premium "AI Control Room", AppShell, Sidebar, TanStack Query
- Pagine navigabili end-to-end: login demo → Project Hub → Control Room → Integration Center (React Flow graph)
- Routing frontend e pagine collegate all'API via `VITE_API_URL`
- Health check API
- PostgreSQL con SQLAlchemy async + Alembic (schema foundation + Shopify)
- CRUD progetti (`POST/GET /api/projects`, dettaglio)
- Integrazioni per progetto: merge di 8 provider (anche non collegati → `not_connected`)
- **Shopify Sync v2**: OAuth connect, sync paginato prodotti/ordini/varianti/line items, attribution first-last touch, dashboard KPI da DB normalizzato
- **Shopify Dashboard v2**: E-commerce Control Room con product intelligence, inventory risk, order operations, SEO opportunities, alert center, daily diagnosis e attribution intelligence (Shopify-only; GA4/Meta/Google Ads/Klaviyo in roadmap)
- **Content SEO Engine Foundation**: sync contenuti Shopify, audit legacy
- **Product & Collection SEO Optimizer**: score trasparente, modal Modifica SEO (campi precompilati, badge stato), proposta manuale/AI con preview e approve/apply controllato
- **Brand Intelligence Foundation**: profilo brand, wizard, knowledge score, context builder AI, integrazione SEO non distruttiva
- **Brand Intelligence Import AI v1**: upload documenti, extracted facts review, apply controllato
- **Brand Intelligence Import Jobs v0.2.2**: batch persistenti, progress async, conflict detection, storico import
- **Brand Intelligence AI Synthesis v0.2.3**: bozze per sezione, review strutturata, apply controllato
- **Brand Intelligence Source Enrichment v0.2.4**: sito, social, recensioni nell'import AI
- **Changelog Alpha**: versioning `0.x.x-alpha` — vedi [`CHANGELOG.md`](CHANGELOG.md) e `/projects/:id/changelog`
- Struttura connectors e skills (stub OAuth per altri provider)

Non ancora implementato: autenticazione utenti, OAuth altri provider, sync automatico, generazione/publish articoli blog Shopify, Editorial SEO (blog/ricette), provider oltre Shopify.

**Env opzionali SEO Optimizer**: `OPENAI_API_KEY`, `OPENAI_MODEL` (default `gpt-4o-mini`). Apply su Shopify richiede scope `write_products` (riconnessione OAuth).
