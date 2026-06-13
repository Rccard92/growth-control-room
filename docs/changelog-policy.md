# Changelog Policy — Growth Control Room (Alpha)

## Fase attuale

Growth Control Room è in **fase Alpha**. Le versioni seguono il formato:

`0.MINOR.PATCH-alpha`

Esempio: `0.1.1-alpha`

Non usiamo versioni `1.x` finché il prodotto non esce da Alpha verso Beta/GA.

## Quando incrementare

### Major (`0.x` → cambio di fase o architettura)

Riservato a:

- Passaggio Alpha → Beta o GA
- Refactor architetturale che cambia flussi core (auth, sync, data model pubblico)
- Breaking change su API o UX che richiede migrazione esplicita

In Alpha raro; preferire minor/patch con nota breaking in changelog.

### Minor (`0.1.x` → `0.2.0`)

Nuove funzionalità rilevanti:

- Nuovo modulo (es. Editorial SEO, nuovo connector)
- Nuova area prodotto con workflow end-to-end
- Estensioni significative a moduli esistenti

### Patch (`0.1.1` → `0.1.2`)

Fix, miglioramenti UI, refactor non distruttivo:

- Bug fix
- UX improvement (modal, badge, copy)
- Performance, logging, documentazione
- Adattamenti skill/regole senza cambio contratto API

## Regole pratiche

1. **Non aumentare la versione a ogni micro-fix** — raggruppare modifiche affini in una release logica.
2. **Una voce changelog = un beneficio utente/dev**, non ogni commit.
3. **Data ISO** (`YYYY-MM-DD`) per ogni release.
4. **Tipo release** esplicito: Alpha minor / Alpha patch.
5. Aggiornare [`CHANGELOG.md`](../CHANGELOG.md) e [`apps/web/src/constants/changelog.ts`](../apps/web/src/constants/changelog.ts) insieme.

## Esempi

| Modifica | Versione |
|----------|----------|
| Fix typo in README | Nessuna (o accumula in patch) |
| Nuova modal SEO + badge campi | `0.1.1-alpha` patch |
| Nuovo modulo Blog Shopify | `0.2.0-alpha` minor |
| Passaggio a Beta pubblica | `0.9.0-beta` o `1.0.0-beta` (decisione team) |

## File correlati

- [`CHANGELOG.md`](../CHANGELOG.md) — storico release
- UI Changelog — `/projects/:id/changelog`
