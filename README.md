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
| `DATABASE_URL` | `postgresql+asyncpg://gcr:gcr_dev@localhost:5432/growth_control_room` | Connessione PostgreSQL |
| `CORS_ORIGINS` | `*` | Origini CORS consentite (separate da virgola) |
| `APP_ENV` | `production` | Ambiente applicazione (`development` in locale) |

## Deploy su Railway

Due servizi separati: **API** (FastAPI) e **WEB** (Vite preview).

### Servizio API

| Variabile | Esempio |
|-----------|---------|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` — se Railway fornisce `postgresql://`, la config lo converte in `postgresql+asyncpg://` |
| `CORS_ORIGINS` | `https://web-xxx.up.railway.app` |
| `APP_ENV` | `production` |

Il container API esegue `alembic upgrade head` all'avvio, poi uvicorn.

### Servizio WEB

| Variabile | Esempio |
|-----------|---------|
| `VITE_API_URL` | `https://api-xxx.up.railway.app` |

`VITE_API_URL` è una variabile di **build**: impostala prima del deploy o forza un rebuild dopo averla aggiunta.

Lascia vuoto lo Start Command su entrambi i servizi (usa il CMD del Dockerfile).

### Post-deploy

1. Redeploy API (migration 002 + seed demo)
2. Redeploy WEB con `VITE_API_URL` impostato all'URL pubblico dell'API

## Documentazione

- [Architettura](docs/architecture.md)
- [Integrazioni](docs/integrations.md)

## Stato attuale

Implementato:

- Routing frontend e pagine collegate all'API via `VITE_API_URL`
- Health check API
- PostgreSQL con SQLAlchemy async + Alembic (schema foundation, 7 entità)
- CRUD progetti (`POST/GET /api/projects`, dettaglio)
- Integrazioni per progetto: merge di 8 provider (anche non collegati → `not_connected`)
- Struttura connectors e skills (stub, senza OAuth)

Non ancora implementato: autenticazione, OAuth integrazioni, sync dati, Shopify/content layer.
