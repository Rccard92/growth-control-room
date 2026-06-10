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
| `CORS_ORIGINS` | `*` | Origini CORS consentite (separate da virgola) |
| `APP_ENV` | `production` | Ambiente applicazione (`development` in locale) |

## Deploy su Railway

Due servizi separati: **API** (FastAPI) e **WEB** (Vite preview).

### Servizio API

| Variabile | Esempio |
|-----------|---------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (**obbligatoria** sul servizio API) |
| `CORS_ORIGINS` | `https://web-xxx.up.railway.app` |
| `APP_ENV` | `production` |

`DATABASE_URL` deve essere impostata sul servizio **API**, non solo sul database Postgres. Senza questa variabile il container fallisce all'avvio con un errore esplicito. Railway fornisce spesso `postgresql://` o `postgres://`; la config converte automaticamente per asyncpg (FastAPI) e psycopg (Alembic).

Il container API esegue `alembic upgrade head` all'avvio, poi uvicorn.

### Servizio WEB

| Variabile | Esempio |
|-----------|---------|
| `VITE_API_URL` | `https://api-xxx.up.railway.app` (senza `/api` finale) |
| `WEB_ALLOWED_HOSTS` | *(opzionale)* Host aggiuntivi per `vite preview`, separati da virgola (es. dominio custom) |

`VITE_API_URL` è una variabile di **build**: imposta l'URL base dell'API **senza** suffisso `/api` (es. `https://api-xxx.up.railway.app`, non `.../api`). Il frontend aggiunge automaticamente i path `/api/projects`, ecc. Rebuild obbligatorio dopo ogni modifica.

Se Railway assegna un nuovo dominio o usi un custom domain, aggiungilo in `WEB_ALLOWED_HOSTS` sul servizio WEB (runtime). L'host Railway attuale è già incluso in config.

Lascia vuoto lo Start Command su entrambi i servizi (usa il CMD del Dockerfile).

### Post-deploy

1. Redeploy API (migration 003 + seed demo)
2. Redeploy WEB con `VITE_API_URL` impostato all'URL pubblico dell'API

## Integrazione Shopify (Custom App)

Connessione manuale read-only via Admin API access token (no OAuth in v1).

### Creare la Custom App su Shopify

1. Shopify Admin → **Settings** → **Apps and sales channels** → **Develop apps**
2. **Create an app** → nome a scelta (es. Growth Control Room)
3. **Configure Admin API scopes**:
   - `read_products`
   - `read_orders`
   - *(step successivo blog)* `write_content`, `write_online_store_pages`
4. **Install app** sullo store
5. Copia **Admin API access token** (`shpat_...`) e il dominio `nomesito.myshopify.com`

### Connettere da Growth Control Room

1. Apri un progetto → **Integrazioni** → Shopify → **Connetti**
2. Inserisci dominio shop e Admin API access token
3. Dopo la connessione, usa **Sincronizza dati Shopify** per importare prodotti e ordini

Endpoint API:

- `POST /api/projects/{id}/integrations/shopify/connect`
- `GET /api/projects/{id}/shopify/status`
- `POST /api/projects/{id}/shopify/sync`
- `GET /api/projects/{id}/shopify/dashboard`

## Documentazione

- [Architettura](docs/architecture.md)
- [Integrazioni](docs/integrations.md)

## Stato attuale

Implementato:

- **Frontend Foundation v1**: UI dark premium "AI Control Room", AppShell, Sidebar, TanStack Query
- Pagine navigabili end-to-end: login demo → Project Hub → Control Room → Integration Center (React Flow graph)
- Routing frontend e pagine collegate all'API via `VITE_API_URL`
- Health check API
- PostgreSQL con SQLAlchemy async + Alembic (schema foundation + Shopify)
- CRUD progetti (`POST/GET /api/projects`, dettaglio)
- Integrazioni per progetto: merge di 8 provider (anche non collegati → `not_connected`)
- **Shopify v1**: connect manuale (Custom App token), sync read-only prodotti/ordini, dashboard KPI
- SEO Content Room e AI Brief: placeholder evoluti con roadmap
- Struttura connectors e skills (stub OAuth per altri provider)

Non ancora implementato: autenticazione utenti, OAuth integrazioni, sync automatico, creazione articoli blog Shopify, provider oltre Shopify.
