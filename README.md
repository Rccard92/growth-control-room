# Growth Control Room

Piattaforma multi-brand per monitorare progetti e-commerce e marketing.

Ogni utente può creare più progetti. Ogni progetto può collegare integrazioni diverse: Shopify, Meta Ads, Google Ads, Klaviyo, Google Search Console, GA4, Merchant Center e TikTok.

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

### 4. Avvia backend e frontend

```bash
pnpm dev
```

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Health check: http://localhost:8000/api/health

### Avvio singolo

```bash
pnpm dev:web   # solo frontend
pnpm dev:api   # solo backend
```

## Variabili d'ambiente

Copia `.env.example` in `.env` e adatta i valori se necessario.

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://gcr:gcr_dev@localhost:5432/growth_control_room` | Connessione PostgreSQL |
| `CORS_ORIGINS` | `http://localhost:5173` | Origini CORS consentite |

## Documentazione

- [Architettura](docs/architecture.md)
- [Integrazioni](docs/integrations.md)

## Stato attuale

Scaffolding iniziale con:

- Routing frontend e pagine placeholder
- Health check API
- Struttura connectors e skills (stub, senza OAuth)
- PostgreSQL via Docker Compose

Non ancora implementato: autenticazione, OAuth, logica integrazioni reali, persistenza DB.
