# Roadmap — da SEO Room a Growth Control Room

**Versione:** 1.0 — 2026-09-18
**Base:** [`audit-2026-09.md`](audit-2026-09.md)

Obiettivo finale: una control room che raccolga in un unico flusso i dati di Shopify,
suite Google, Meta Ads, TikTok Ads e Klaviyo, li normalizzi in metriche confrontabili, li
sorvegli in continuo e ci metta sopra un agente AI che dica — con evidenze — *questa
campagna sta peggiorando, la frequenza è salita a 3.8, il CPL è +42% in 7 giorni, taglia*,
oppure *questo adset ha CPA 30% sotto target da 5 giorni con volume stabile, scala del 20%*.

## Come leggere questo piano

- Le fasi sono **sequenziali per dipendenza**, non per preferenza. La Fase 1 non si può
  saltare: tutto ciò che viene dopo poggia sul modello metriche.
- Le stime sono in **settimane-persona**, calibrate su 1 sviluppatore full-time con
  l'attuale velocità del repo. Con 2 persone, le Fasi 2 e 3 parallelizzano bene.
- Ogni fase ha una **Definition of Done** verificabile. Se la DoD non passa, la fase non
  è chiusa: è la regola che impedisce l'accumulo di debito già visibile nel progetto.
- ⛔ = blocca l'uso con clienti reali. Da fare comunque, prima di tutto il resto.

| Fase | Titolo | Stima | Dipende da |
|---|---|---|---|
| 0 | Messa in sicurezza e fondamenta di processo | 3-4 sett. | — |
| 1 | Livello dati unificato e job runner | 4-5 sett. | 0 |
| 2 | Connettori paid media e CRM | 6-8 sett. | 1 |
| 3 | Livello semantico, blended metrics e attribuzione | 3-4 sett. | 2 |
| 4 | Motore di alerting e anomaly detection | 3-4 sett. | 3 |
| 5 | Agente AI di controllo | 4-6 sett. | 4 |
| 6 | Azioni e automazione (write-back) | 4-5 sett. | 5 |
| 7 | Prodotto, scala e go-to-market | 4-6 sett. | 6 |
| — | **Totale** | **31-42 sett.** | |

Consolidamento del debito esistente (§ Fase 8) va spalmato, non accodato.

---

## Fase 0 — Messa in sicurezza e fondamenta di processo ⛔

**Perché prima di tutto:** oggi l'API è pubblica, senza autenticazione, e conserva token
scrivibili di Shopify e Google in base64. Ogni settimana di sviluppo aggiuntivo su questa
base moltiplica il costo del retrofit (211 endpoint da proteggere, tutte le query da
filtrare per tenant).

### 0.1 Autenticazione e autorizzazione

- Auth backend: JWT access token breve (15 min) + refresh token httpOnly con rotazione,
  oppure sessioni server-side con Redis. Password con `argon2id`.
- Dependency FastAPI `get_current_user` applicata **a tutto** tranne health, OAuth callback
  e privacy. Test di guardia: uno che scorre `app.routes` e fallisce se un endpoint non
  ha la dependency in whitelist esplicita.
- Modello ruoli minimo: `owner`, `admin`, `editor`, `viewer` a livello di workspace;
  `editor` è il minimo per apply/publish; `viewer` è sola lettura.
- Login reale sul frontend, `AuthProvider`, route protette, refresh silenzioso,
  logout, gestione 401 globale in `lib/api.ts`.
- Rimuovere o proteggere `GET /api/debug/routes`.

### 0.2 Multi-tenancy vera

- Propagare `workspace_id` da `current_user` in tutte le query; eliminare
  `get_default_workspace()`.
- Aggiungere il vincolo a livello DB dove manca, e valutare **Row-Level Security Postgres**
  come rete di sicurezza (`SET app.current_workspace` per sessione).
- `users ↔ workspaces` come many-to-many (`workspace_members` con ruolo), non 1-1.
- Migration dati: assegnare i progetti esistenti al workspace di default e al primo utente.
- Test di isolamento tenant: utente A non deve vedere né toccare risorse di B, su ogni
  famiglia di endpoint.

### 0.3 Cifratura reale dei segreti

- Sostituire `encryption.py` con **Fernet** (`cryptography`) con chiave da
  `SECRETS_ENCRYPTION_KEY`, o KMS se si va su cloud gestito.
- Supportare la **rotazione**: `MultiFernet` con lista di chiavi, prefisso di versione nel
  payload (`v2:...`), migration che ricifra i payload `plain:` esistenti.
- ⚠️ **Rotazione obbligatoria dei token già emessi.** Tutto ciò che è stato in base64 in un
  DB accessibile va considerato compromesso: revocare e riconnettere Shopify e Google.
- Vietare il log di payload decifrati (test + code review).

### 0.4 Hardening infrastruttura

- `CORS_ORIGINS` senza default `*`: in produzione il valore è obbligatorio, l'app non parte
  se manca (stesso pattern già usato per `DATABASE_URL`).
- Rate limiting applicativo (`slowapi` o middleware su Redis): limiti per IP su login, per
  utente su endpoint AI e sync.
- `Dockerfile.web` multi-stage → build statica servita da **nginx** o **Caddy** con gzip/brotli,
  header di cache, `Content-Security-Policy`, `X-Frame-Options`, HSTS. Via `vite preview`.
- `Dockerfile.api` multi-stage, utente non-root, healthcheck.
- Migration fuori dal comando di avvio: job di release dedicato, o lock advisory Postgres
  per rendere `alembic upgrade` sicuro con repliche multiple.
- Rimuovere `uv.lock` da `.gitignore` e committarlo.

### 0.5 Qualità automatica

- **CI GitHub Actions**: su ogni PR → `ruff check` + `ruff format --check` + `mypy` (modalità
  graduale) + `pytest` con Postgres di servizio + `tsc -b` + `vitest` + `pnpm build`.
- `conftest.py` con fixture env, factory di sessione e database di test; `pyproject.toml`
  con `[tool.pytest.ini_options]` (`asyncio_mode = "auto"`, `testpaths`).
- ESLint + Prettier sul frontend, `pre-commit` per entrambi gli stack.
- **Sistemare i 9 test rotti** con `freezegun` o un clock iniettabile: mai più date
  hardcoded relative a "oggi".
- Branch protection: niente merge su `main` con CI rossa.

### 0.6 Osservabilità minima

- Logging strutturato JSON con `request_id`, `workspace_id`, `user_id`, `project_id`.
- Error tracking (Sentry o simile) su API e frontend.
- `/api/health` esteso: stato DB, migration applicate, versione, stato broker.

**Definition of Done Fase 0**
- [ ] Nessun endpoint non whitelisted risponde senza token valido (test automatico)
- [ ] Un utente non accede a dati di un altro workspace (test automatico)
- [ ] Nessun segreto a riposo in formato decodificabile senza chiave
- [ ] Token Shopify/Google ruotati dopo la migrazione a Fernet
- [ ] CI verde obbligatoria; suite backend e frontend **al 100% verde**
- [ ] Frontend servito da nginx/Caddy, API non-root, migration idempotenti con lock

---

## Fase 1 — Livello dati unificato e job runner

**Perché:** è il vero cuore della "convergenza in un unico flusso". Farlo dopo i connettori
significa riscrivere i connettori.

### 1.1 Framework connettori reale

Rifondare `packages/connectors` (oggi 100% morto) come contratto effettivamente usato dall'API,
e **migrarci dentro Shopify e Google** che oggi vivono in `apps/api/app/services/`.

```python
class BaseConnector(ABC):
    provider: IntegrationProvider
    capabilities: frozenset[Capability]     # ads | commerce | analytics | email | search

    async def authorize_url(self, ctx) -> str: ...
    async def exchange_code(self, ctx, code: str) -> Credentials: ...
    async def refresh(self, creds: Credentials) -> Credentials: ...
    async def health_check(self, ctx) -> ConnectorHealth: ...

    # ingestion incrementale, idempotente, riprendibile
    async def fetch_entities(self, ctx, since: datetime) -> AsyncIterator[EntityBatch]: ...
    async def fetch_metrics(self, ctx, window: DateWindow) -> AsyncIterator[MetricBatch]: ...

    # opzionale, dichiarato da capabilities
    async def apply_action(self, ctx, action: ConnectorAction) -> ActionResult: ...
```

Servizi trasversali da fornire **una volta sola**, non per connettore:
- rate limiter per provider (token bucket persistito su Redis, consapevole dei limiti
  specifici: cost-based per Shopify, per-app per Meta, QPS per TikTok);
- retry con backoff esponenziale + jitter, rispetto di `Retry-After`;
- circuit breaker per provider;
- cursori di sync persistiti (`sync_state`) per ingestion incrementale;
- normalizzazione valuta e timezone;
- logging costi/quote per provider, sullo stesso modello già usato per DataForSEO.

### 1.2 Modello dati delle metriche

Il principio: **entità normalizzate + una fact table giornaliera per grana**, non una
tabella per provider. Tutte le nuove tabelle hanno `workspace_id` e `project_id`.

```sql
-- Anagrafica account collegati (un progetto può avere più account per provider)
ad_accounts(id, project_id, provider, external_id, name, currency, timezone,
            status, connected_at, last_synced_at)

-- Gerarchia paid, uguale per Meta / Google Ads / TikTok
ad_campaigns(id, ad_account_id, external_id, name, objective, status,
             budget_amount, budget_type, start_at, end_at, raw_payload)
ad_groups  (id, campaign_id, external_id, name, status, optimization_goal,
            bid_strategy, targeting_summary, raw_payload)   -- adset | ad group
ads        (id, ad_group_id, external_id, name, status, creative_id, landing_url,
            utm_source, utm_medium, utm_campaign, utm_content, raw_payload)
ad_creatives(id, ad_account_id, external_id, type, thumbnail_url, body_text,
             headline, first_seen_at, content_hash)

-- Fact table unica, partizionata per mese su `date`
ad_metrics_daily(
  id, project_id, provider, entity_level,        -- account|campaign|ad_group|ad
  entity_id, date, currency,
  spend, impressions, reach, frequency, clicks, link_clicks,
  video_views_3s, video_views_25, video_views_75, thruplays,
  conversions, conversion_value, leads, purchases, add_to_carts,
  initiated_checkouts, landing_page_views,
  attribution_window, raw_payload, ingested_at,
  UNIQUE(provider, entity_level, entity_id, date, attribution_window)
)

-- Analytics (GA4), già parzialmente presente ma non persistito come serie
analytics_daily(project_id, date, channel_group, source, medium, campaign,
                landing_page, device, sessions, users, new_users, engaged_sessions,
                bounce_rate, conversions, revenue, item_views, add_to_carts, checkouts)

-- Search organico (GSC), oggi calcolato ma non storicizzato
search_console_daily(project_id, date, page, query, country, device,
                     clicks, impressions, ctr, position)

-- Email/SMS (Klaviyo)
email_campaigns(id, project_id, external_id, name, type, channel, sent_at, list_ids)
email_flows(id, project_id, external_id, name, status, trigger_type)
email_metrics_daily(project_id, date, entity_level, entity_id, recipients, delivered,
                    opens, unique_opens, clicks, unique_clicks, unsubscribes,
                    spam_complaints, bounces, orders, revenue)

-- Commerce: generalizzare shopify_daily_metrics
commerce_daily(project_id, date, currency, orders, gross_sales, discounts, refunds,
               taxes, shipping, net_sales, total_sales, units, new_customers,
               returning_customers, aov, sessions, conversion_rate)

-- Stato di ingestion per riprendibilità e osservabilità
sync_state(project_id, provider, stream, cursor, last_success_at,
           last_error, consecutive_failures, backfill_completed_through)
sync_runs(id, project_id, provider, stream, status, window_start, window_end,
          rows_ingested, started_at, finished_at, error_message)
```

Scelte da fissare subito, perché costose da cambiare dopo:
- **Timezone**: ogni `date` è nel fuso dell'account sorgente, con il fuso salvato accanto;
  il layer semantico (Fase 3) riallinea al fuso del progetto.
- **Valuta**: si salva la valuta nativa **e** l'importo convertito con il tasso del giorno
  (`fx_rates(date, base, quote, rate)`), mai solo il convertito.
- **Restatement**: i dati pubblicitari cambiano retroattivamente (conversioni in ritardo).
  Il sync riscrive sempre una finestra mobile (es. ultimi 7-28 giorni), con upsert
  idempotente sulla chiave unica.
- **Finestre di attribuzione**: `attribution_window` fa parte della chiave, così si può
  confrontare 7d-click vs 1d-view senza sovrascrivere.
- **Partizionamento** di `ad_metrics_daily` per mese fin da subito, più indici su
  `(project_id, date)` e `(entity_id, date)`.

### 1.3 Job runner e scheduler

Sostituire `asyncio.create_task` con un'infrastruttura vera.

- Broker Redis + worker **ARQ** (nativo async, leggero, coerente con lo stack) oppure
  Celery se si prevede fan-out complesso. Servizio worker separato su Railway.
- Coda per priorità: `interactive` (audit on-demand, generazioni AI), `sync` (ingestion),
  `maintenance` (rollup, retention).
- Scheduler: sync automatico per progetto — ads e analytics ogni ora, commerce ogni 15-30
  minuti, search console giornaliero (l'API ha 2-3 giorni di ritardo), backfill iniziale a 13 mesi.
- Ogni job: idempotente, con lock per `(project_id, provider, stream)`, retry con backoff,
  timeout, e una riga in `sync_runs`.
- Recovery all'avvio: job in `running` più vecchi del timeout tornano in coda.
- **Migrare i job esistenti** (Growth Audit, batch editoriali, SEO skill run) sulla stessa
  infrastruttura: elimina in un colpo la criticità 4.4 dell'audit.

### 1.4 UI di stato dell'ingestion

Pagina "Data Health" per progetto: per ogni provider, ultimo sync riuscito, freschezza
dei dati, righe ingerite, errori recenti, copertura del backfill, azione "risincronizza
intervallo". Senza questa pagina, i dati sbagliati sembrano dati veri.

**Definition of Done Fase 1**
- [ ] Shopify e Google migrati sul `BaseConnector`, `packages/connectors` non contiene stub
- [ ] Nessun `asyncio.create_task` residuo per lavoro persistente
- [ ] Sync schedulati che girano da soli e sopravvivono a un restart a metà
- [ ] Rieseguire lo stesso sync due volte non duplica righe (test di idempotenza)
- [ ] `commerce_daily` popolato da Shopify, `analytics_daily` da GA4, `search_console_daily` da GSC
- [ ] Pagina Data Health con freschezza per provider

---

## Fase 2 — Connettori paid media e CRM

Ordine consigliato per valore/sforzo: **Meta Ads → Klaviyo → Google Ads → TikTok Ads**.

### 2.1 Meta Ads (3-4 settimane)

Il più importante e il più oneroso.

- App Meta Business + **App Review** per `ads_read`, `ads_management` (per la Fase 6),
  `business_management`. La review richiede screencast, privacy policy, use case scritto:
  **avviarla all'inizio della Fase 2**, non alla fine — i tempi sono di settimane.
- OAuth Facebook Login for Business, long-lived token (60 giorni) con rinnovo automatico e
  allarme di scadenza; selezione di Business Manager e ad account.
- Ingestion via **Insights API**: gerarchia account/campaign/adset/ad, creatività,
  metriche giornaliere con breakdown. Per volumi grandi usare i **job asincroni** di Insights
  (`async_job`), non le chiamate sincrone.
- Metriche obbligatorie per la visione del prodotto: `spend`, `impressions`, `reach`,
  **`frequency`**, `cpm`, `ctr` (all e link), `cpc`, `actions` (purchase, lead,
  add_to_cart, initiate_checkout), `action_values`, `purchase_roas`, `video_thruplay`,
  `video_p25/p75`, `cost_per_action_type` (da cui **CPL** e **CPA**).
- Gestire il rate limiting Meta (header `X-Business-Use-Case-Usage`) e i restatement.
- Breakdown per placement, device, età/genere: utili all'agente, costosi in righe —
  tenerli su una tabella separata e a granularità campagna, non ad.

### 2.2 Klaviyo (1-1.5 settimane)

Il più semplice: API key o OAuth, REST v2024+, rate limit generosi.

- Campagne, flow, metriche di invio, revenue attribuita, liste e segmenti, size nel tempo.
- Metriche prodotto: revenue per email, `open rate`, `click rate`, `unsub rate`,
  `revenue per recipient`, quota di fatturato email/SMS sul totale.

### 2.3 Google Ads (2-2.5 settimane)

- Richiede un **developer token** approvato da Google (basic access): anche qui, richiesta
  da avviare subito. Lo scope `adwords` è **già richiesto in OAuth** oggi ma inutilizzato:
  il flusso di consenso esiste già, manca l'implementazione.
- `google-ads` Python client, GAQL su `customer`, `campaign`, `ad_group`, `ad_group_ad`,
  `asset`; gestione MCC e customer id di login.
- Metriche: cost, impressions, clicks, conversions, conversions_value, search impression
  share, quality score, **Performance Max asset group** (grana diversa: prevederla nel modello).

### 2.4 TikTok Ads (1.5-2 settimane)

- TikTok for Business API, OAuth, Reporting API sincrono e asincrono.
- Gerarchia campaign/adgroup/ad, metriche spend/impression/click/conversion/video.

### 2.5 GA4 esteso (0.5-1 settimana)

Riutilizzare il client esistente per **storicizzare** `analytics_daily` invece di calcolare
on-demand: canali, sorgenti, landing page, device, funnel ecommerce (già implementato per
l'audit) — così diventa serie storica confrontabile con la spesa.

**Definition of Done Fase 2**
- [ ] Ogni provider si connette, rinnova il token da solo e segnala la scadenza imminente
- [ ] Backfill a 13 mesi completato senza intervento manuale
- [ ] `ad_metrics_daily` popolato dai 3 provider ads con la stessa semantica
- [ ] Riconciliazione: spend per campagna a pari data coincide con la UI nativa entro l'1%
- [ ] Test con mock di risposte reali per rate limit, token scaduto, restatement

---

## Fase 3 — Livello semantico, blended metrics e attribuzione

I dati grezzi di quattro piattaforme non sono confrontabili. Questa fase li rende una
cosa sola, ed è ciò che il committente chiama "un unico flusso".

### 3.1 Dizionario delle metriche

Un registry **unico e versionato** (codice + tabella, sulla falsariga dell'ottimo
`operation_registry.py` già presente) che definisce ogni metrica: formula, unità, grana
minima, direzione buona/cattiva, provider che la supportano, come si aggrega nel tempo
(somma vs media pesata — errore classico: mediare i CPM invece di ricalcolarli).

Metriche derivate obbligatorie:
`CPM`, `CPC`, `CTR`, `CPA`, **`CPL`**, `ROAS`, `AOV`, `conversion rate`,
**`frequency`**, `hook rate` (3s/impression), `hold rate` (thruplay/3s),
`cost per add-to-cart`, `spend share`, `revenue share`.

E le metriche **blended**, che sono il motivo per cui la control room esiste:
- `blended ROAS` = fatturato Shopify totale / spesa pubblicitaria totale
- `MER` = revenue / total marketing spend, `aMER` = revenue nuovi clienti / spend
- `CAC` e `nCAC` (solo nuovi clienti, incrociando i clienti Shopify)
- `contribution margin` se si aggiungono i COGS (vedi 3.4)

### 3.2 Modello a stelle e rollup

- Viste/tabelle materializzate: `fact_channel_daily` (canale × giorno), `fact_project_daily`
  (totale progetto × giorno), `fact_product_daily` (prodotto × giorno, unendo Shopify,
  GA4 item e ads a livello di campagna quando mappabile).
- Rollup settimanali e mensili precalcolati per le dashboard.
- Rigenerazione incrementale nella finestra dei restatement.

### 3.3 Attribuzione

Tre livelli, in ordine di onestà crescente:
1. **Platform-reported** (quello che ogni piattaforma dichiara di aver generato) — sempre
   mostrato, sempre etichettato come tale, e sempre con la somma confrontata al fatturato
   reale (la somma supera quasi sempre il 100%: mostrarlo esplicitamente è un valore).
2. **UTM last non-direct** dai dati ordine Shopify — già presenti nel progetto
   (`first/last touch` su `shopify_orders`), da collegare alle campagne via matching UTM.
3. **Blended / MER** come verità di riferimento per le decisioni di budget.

Prevedere una tabella `attribution_mapping` per il matching UTM↔campagna, con regole di
normalizzazione e una UI per le eccezioni: le UTM del mondo reale sono sporche.

### 3.4 Dati di costo (opzionale ma ad alto valore)

Import COGS a livello di variante (CSV o metafield Shopify) + costi di spedizione e fee:
sblocca il **margine di contribuzione** e trasforma "questa campagna ha ROAS 2.1" in
"questa campagna perde 4€ a ordine", che è la decisione vera.

**Definition of Done Fase 3**
- [ ] Una sola query restituisce spend, revenue, ROAS, CPA per qualsiasi canale e periodo
- [ ] Le metriche derivate sono ricalcolate dalle componenti, mai mediate
- [ ] Il confronto platform-reported vs blended è esposto e spiegato in UI
- [ ] Le dashboard rispondono in <500ms su 13 mesi di dati

---

## Fase 4 — Motore di alerting e anomaly detection

Qui il prodotto smette di essere una dashboard e inizia a sorvegliare. Nota: la tabella
`alerts` esiste già nello schema e non è mai stata scritta — questa fase la riscrive
com'era da prevedere.

### 4.1 Modello

```sql
alert_rules(id, project_id, name, enabled, scope_level, scope_filter,
            metric_key, comparator, threshold_type,      -- static | pct_change | zscore | forecast
            threshold_value, baseline_window_days, comparison_window_days,
            min_spend_guard, min_conversions_guard, min_impressions_guard,
            severity, cooldown_hours, channels, created_by)
alert_events(id, rule_id, project_id, entity_level, entity_id, entity_name,
             triggered_at, metric_value, baseline_value, delta_pct, severity,
             status,                                      -- open | acknowledged | resolved | muted
             dedupe_key, evidence_json, resolved_at, resolved_reason)
alert_notifications(id, alert_event_id, channel, sent_at, status, error)
alert_subscriptions(user_id, project_id, channels, min_severity, quiet_hours)
```

### 4.2 Regole di partenza (le richieste esplicitamente dal committente)

| Regola | Condizione tipo | Guard |
|---|---|---|
| **Frequenza in crescita** | `frequency` 7d > 2.5 **e** +25% vs 7d precedenti | spend ≥ soglia |
| **CPL/CPA in salita** | `cost_per_lead` 3d > +30% vs baseline 14d | ≥ 10 conversioni nella baseline |
| **ROAS in calo** | `roas` 3d < 70% della baseline 14d | spend 3d ≥ soglia |
| **CTR in calo (creative fatigue)** | `ctr` -25% vs baseline **e** frequenza in crescita | impression ≥ soglia |
| **CPM in impennata** | `cpm` +35% vs baseline 14d | — |
| **Budget non speso** | spesa < 70% del budget giornaliero per 2 giorni | campagna attiva |
| **Spesa fuori controllo** | spesa giornaliera > 150% della media 7d | — |
| **Vincente da scalare** | CPA ≤ 80% del target **e** volume stabile per ≥ 4 giorni **e** frequenza < 2 | conversioni ≥ soglia |
| **Crollo conversion rate sito** | CR 3d -25% vs baseline, a traffico stabile | sessioni ≥ soglia |
| **Stock a rischio su prodotto in spinta** | giorni di copertura < 14 su prodotto con spend attivo | — |
| **Feed Merchant in errore** | disapprovazioni in aumento | già disponibile via Merchant Center |
| **Calo traffico organico** | click GSC 7d -20% vs 7d precedenti | — |
| **Ingestion ferma** | nessun sync riuscito da > 3 ore per un provider | — |

### 4.3 Rilevamento statistico (oltre le soglie fisse)

- Baseline robusta: mediana mobile + MAD (non media e deviazione standard: le metriche ads
  hanno code pesanti e outlier veri).
- **Correzione per stagionalità settimanale**: confrontare lunedì con lunedì. Senza questa,
  il lunedì mattina il sistema urla ogni settimana e nessuno lo ascolta più.
- Significatività: nessun alert sotto un minimo di spesa, conversioni e impression —
  un CPL che passa da 1 a 2 conversioni non è un segnale.
- **Anti-rumore**: deduplica per `dedupe_key`, cooldown per regola/entità, raggruppamento
  gerarchico (se 8 adset della stessa campagna peggiorano, un alert sulla campagna, non otto),
  auto-risoluzione quando la condizione rientra.
- Severità calcolata da impatto economico stimato (€ a rischio), non dalla sola deviazione.

### 4.4 Consegna

- Centro alert in-app con stati, assegnazione, note.
- Email digest giornaliero + notifiche immediate per severità critica.
- Webhook generico → Slack/Telegram/WhatsApp Business.
- Preferenze per utente, quiet hours.

**Definition of Done Fase 4**
- [ ] Le regole girano schedulate e producono eventi persistiti
- [ ] Backtest su dati storici: ogni regola viene validata su 90 giorni reali, con conteggio
      di veri/falsi positivi documentato prima dell'attivazione
- [ ] Un alert critico raggiunge il destinatario in meno di 15 minuti dal dato
- [ ] Meno di ~5 alert al giorno per progetto a regime (metrica di prodotto, non tecnica)

---

## Fase 5 — Agente AI di controllo

Il progetto ha già l'infrastruttura AI giusta (client centralizzato, budget, routing,
context profiles, registry delle operation, skill pack markdown). Qui la si punta sui dati
di performance invece che sui contenuti.

### 5.1 Principio non negoziabile

**L'LLM non calcola le metriche.** Le metriche le calcola SQL, deterministico e testabile.
L'LLM riceve numeri già calcolati e produce: diagnosi, priorità, spiegazione, raccomandazione.
Ogni affermazione dell'agente deve essere tracciabile a una riga di dati (`evidence_json`).
Questo è anche l'unico modo per tenere i costi sotto controllo.

### 5.2 Componenti

**Context builder di performance** — l'equivalente del `BrandIntelligenceContextBuilder`
per i dati: prende progetto, finestra e scope e produce un pacchetto compatto con KPI,
trend, deltas, anomalie aperte, entità peggiori e migliori, guard di significatività.
Va aggiunto come nuovo `AiContextProfile` (`performance_diagnosis`, `daily_briefing`,
`creative_analysis`), coerente con l'architettura esistente.

**Agente diagnostico** — dato un alert o un'entità: perché sta succedendo, cosa è cambiato
(creatività nuova, budget modificato, pubblico saturato, concorrenza, stagionalità, problema
sul sito), quanto è grave in euro, cosa fare, con quale confidenza.

**Playbook** — regole di dominio versionate come skill pack markdown, nello stesso formato
già usato per la SEO (`packages/skills/`):
- `scale-playbook.md` — quando e di quanto scalare (incrementi 20-30%, mai raddoppi su
  adset in learning), come scalare (verticale vs orizzontale), quando duplicare;
- `kill-playbook.md` — soglie di taglio, spesa minima prima di giudicare, differenza tra
  fatica creativa e fatica di pubblico;
- `creative-fatigue.md` — lettura combinata di frequenza, hook rate, CTR, CPM;
- `budget-allocation.md` — riallocazione tra campagne a parità di budget totale;
- `diagnostics.md` — albero diagnostico: CPA su → è CPM, CTR o CR? → e quindi?

**Briefing giornaliero** — un job schedulato che produce ogni mattina: stato di ieri vs
baseline, i 3 problemi che contano, le 3 opportunità, le azioni proposte. Consegnato in-app
e via email. È la funzione che rende il prodotto usato tutti i giorni.

**Chat sui dati** — conversazione sul progetto con tool-calling verso query *predefinite e
parametrizzate* (mai SQL generato dall'LLM), che risponde a "come è andata Meta questa
settimana?" o "quali creatività stanno saturando?".

### 5.3 Costi e affidabilità

- Riusare `ai_usage_logs`, budget guardrail e model routing esistenti: registrare le nuove
  `operation_key` (`agent_daily_briefing`, `agent_diagnose_alert`, ...) nel registry.
- Tier: `cheap` per classificazione e sintesi brevi, `standard` per diagnosi, `premium`
  solo per il briefing giornaliero.
- **Completare il pricing Claude** in `pricing.py` (oggi è un TODO: le chiamate Anthropic
  risultano a costo zero e non toccano i budget).
- Aggiornare i default di modello, oggi fermi a una generazione precedente.
- Valutazione qualità: set di casi storici con esito noto ("questa campagna è stata tagliata
  ed era giusto"), su cui misurare le raccomandazioni prima di mostrarle come affidabili.

**Definition of Done Fase 5**
- [ ] Ogni numero nel testo generato è tracciabile a una riga di dati
- [ ] Il briefing giornaliero arriva schedulato e costa meno di una soglia definita per progetto
- [ ] L'agente distingue correttamente fatica creativa da saturazione di pubblico su casi reali
- [ ] Nessuna raccomandazione senza guard di significatività soddisfatti

---

## Fase 6 — Azioni e automazione (write-back)

Dalla raccomandazione all'esecuzione. Da fare **solo** dopo che le raccomandazioni si sono
dimostrate affidabili: scalare male in automatico brucia budget reale.

- Scope di scrittura: `ads_management` (Meta), analoghi su Google e TikTok.
- Azioni v1: modifica budget campagna/adset, pausa e riattivazione entità, modifica bid.
- **Flusso ad approvazione** come già fatto bene per il SEO Optimizer (proposta → preview
  → approvazione esplicita → apply): stesso pattern, stessa UX.
- `action_log` completo: chi, quando, cosa, stato precedente, stato nuovo, esito,
  e **rollback con un click**.
- Guardrail di sicurezza: variazione massima giornaliera per entità, tetto di spesa
  complessivo, blacklist di campagne intoccabili, kill switch globale, obbligo di conferma
  sopra soglia.
- Automazione graduale, per livelli: **suggerisci → approva ogni volta → approva per regola
  → automatico con notifica**, configurabile per regola e per progetto.
- Misurazione: ogni azione automatica registra il KPI prima/dopo, così l'efficacia del
  sistema è misurabile e non un atto di fede.

**Definition of Done Fase 6**
- [ ] Nessuna scrittura senza traccia e senza rollback disponibile
- [ ] I guardrail sono testati con tentativi di superamento
- [ ] Modalità automatica attivabile per singola regola, mai globale per default

---

## Fase 7 — Prodotto, scala e go-to-market

- **Multi-brand reale**: vista portfolio su più progetti, confronto tra brand, benchmark interni.
- **Ruoli e permessi granulari**, inviti, audit log accessi.
- **Report**: export PDF/Excel white-label, report cliente schedulato, link condivisibile
  in sola lettura.
- **Onboarding**: wizard di connessione guidato, controllo salute dati, template di alert
  per verticale.
- **Billing** se il prodotto va a mercato: piani, limiti per piano, ribaltamento dei costi
  AI/DataForSEO (l'infrastruttura di usage tracking c'è già ed è pronta a questo).
- **Performance**: code splitting del frontend (oggi 1.56 MB in un chunk), lazy loading
  delle route, virtualizzazione delle tabelle lunghe, caching HTTP.
- **Compliance**: privacy policy sostanziale, DPA, retention configurabile, export ed
  eliminazione dati su richiesta — obbligatorio nel momento in cui si trattano dati di
  clienti terzi in UE.

---

## Fase 8 — Consolidamento del debito (trasversale, continuo)

Da spalmare, riservando ~15-20% di ogni sprint. Non è una fase finale: se lo diventa, non si fa.

| Debito | Intervento | Quando |
|---|---|---|
| `packages/connectors` morto | Assorbito dalla Fase 1.1 | Fase 1 |
| Tabella `alerts` inutilizzata | Sostituita dal modello Fase 4 | Fase 4 |
| `growth-audit-utils.ts` (5.485 righe) | Split per dominio + barrel file | Fase 1-2 |
| `brand_intelligence.py` (94 endpoint in un file) | Split in sub-router per sezione | Fase 2-3 |
| Bundle monolitico 1.56 MB | Code splitting per route | Fase 7 |
| Brand Intelligence legacy (5+ tabelle deprecate) | Decidere: completare o rimuovere, non lasciare a metà | Fase 3 |
| README e `architecture.md` disallineati | Aggiornare a ogni fase chiusa | Continuo |
| Throttling Shopify assente | Risolto dal rate limiter condiviso (Fase 1.1) | Fase 1 |
| SSRF in `source_fetcher.py` | Applicare il validator + risoluzione DNS | Fase 0 |
| Nessuna paginazione sulle liste | Cursor pagination sugli endpoint di lista | Fase 2 |
| URL di produzione hardcoded in `.env.example` | Sostituire con placeholder | Fase 0 |

---

## Decisioni da prendere adesso

Queste scelte condizionano tutto il resto e conviene fissarle prima della Fase 1.

1. **Uno sviluppatore o due?** Le Fasi 2 e 3 sono il collo di bottiglia e parallelizzano
   bene (un connettore a testa). Con 1 persona il piano vale ~8-10 mesi; con 2, ~5-6.
2. **Meta App Review e Google developer token: avviare subito.** Sono processi di
   approvazione esterni che richiedono settimane e non dipendono dal codice. Se partono in
   Fase 0, non bloccano la Fase 2. Se partono in Fase 2, la bloccano.
3. **SaaS multi-cliente o strumento interno?** Cambia la severità della Fase 0 (auth, RLS,
   billing, compliance) e della Fase 7. Se è interno e a un solo utente, la Fase 0 si può
   ridurre — ma cifratura dei token e job runner restano obbligatori in ogni caso.
4. **Congelare SEO/Content.** Le aree SEO, Editorial e Brand Intelligence sono già oltre il
   necessario per un MVP. Ogni settimana spesa lì è una settimana non spesa sul nucleo.
   Proposta: freeze di feature, solo bugfix, fino alla fine della Fase 4.
5. **COGS sì o no.** Se il committente può fornire i costi prodotto, il salto di valore
   (da ROAS a margine) è il più alto del piano rispetto allo sforzo richiesto.

## Il percorso minimo verso il primo valore reale

Se serve dimostrare la visione in fretta, il cammino più corto è:

**Fase 0 (ridotta: auth + cifratura) → Fase 1 → Meta Ads → metriche blended → 5 regole di
alert → briefing giornaliero AI.**

Sono circa **12-15 settimane-persona** e producono già il prodotto che il committente ha
descritto: dati Shopify + Meta in un flusso unico, sorveglianza automatica di frequenza,
CPL e ROAS, e un agente che ogni mattina dice cosa tagliare e cosa scalare. Google Ads,
TikTok, Klaviyo e il write-back si aggiungono dopo su fondamenta già solide.
