# Architettura

Growth Control Room è un monorepo ibrido che combina un frontend React e un backend Python FastAPI, con package condivisi per tipi, UI, connettori e skill AI.

## Panoramica

```mermaid
flowchart TB
  subgraph frontend [Frontend - pnpm]
    Web[apps/web]
    UI[packages/ui]
    SharedTS[packages/shared]
    Web --> UI
    Web --> SharedTS
  end

  subgraph backend [Backend - uv]
    API[apps/api]
    Connectors[packages/connectors]
    Skills[packages/skills]
    API --> Connectors
    API --> Skills
  end

  subgraph infra [Infrastruttura]
    PG[(PostgreSQL)]
  end

  Web -->|"HTTP /api/*"| API
  API --> PG
```

## Struttura monorepo

| Path | Stack | Responsabilità |
|------|-------|----------------|
| `apps/web` | React, Vite, TypeScript | Interfaccia utente, routing, pagine |
| `apps/api` | FastAPI, Python 3.12+ | REST API, orchestrazione integrazioni |
| `packages/shared` | TypeScript | Tipi e costanti condivisi (frontend) |
| `packages/ui` | React | Componenti UI riutilizzabili |
| `packages/connectors` | Python | Connettori per piattaforme esterne |
| `packages/skills` | Python | Skill AI (brief, analisi, automazioni) |

## Toolchain

- **JavaScript**: pnpm workspaces, Node 20+
- **Python**: uv workspace, Python 3.12+
- **Database**: PostgreSQL 16 (Docker Compose)
- **Dev server**: Vite (5173), Uvicorn (8000)

## Flusso dati (futuro)

1. L'utente crea un **progetto** (brand) dalla UI
2. Collega **integrazioni** via OAuth (Shopify, Meta, Google, ecc.)
3. L'API salva i token cifrati in PostgreSQL
4. Job di **sync** invocano i connector in `packages/connectors`
5. I dati aggregati alimentano dashboard e **skill AI** in `packages/skills`

## Convenzioni naming

### TypeScript

- Package scope: `@gcr/shared`, `@gcr/ui`, `@gcr/web`
- Tipi integrazione allineati ai connector Python (`IntegrationType`)

### Python

- Package: `gcr-connectors`, `gcr-skills`, `gcr-api`
- Moduli connector: `connectors.providers.<platform>`
- Registry pattern per lookup dinamico

## API

Tutte le route API sono prefissate con `/api`:

- `GET /api/health` — health check con stato connectors/skills

Il proxy Vite in sviluppo inoltra `/api` verso `localhost:8000`.

## Database

PostgreSQL è avviato via Docker Compose. Lo stub SQLAlchemy in `apps/api/app/core/database.py` è pronto per future migration Alembic, ma non ancora utilizzato.

## Prossimi passi

1. Modelli SQLAlchemy (User, Project, Integration, Credential)
2. Autenticazione JWT o session-based
3. OAuth flow per ogni integrazione
4. Implementazione connector Shopify (primo provider)
5. Skill AI Brief collegata alla pagina `/projects/:id/ai-brief`
