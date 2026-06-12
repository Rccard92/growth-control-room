# Approval Workflow Rules

## Stati proposal

1. **draft** — generata, revisionabile
2. **approved** — approvata da utente, pronta per apply
3. **applied** — scritta su Shopify con successo
4. **rejected** — scartata

## Transizioni consentite

- draft → approved (POST approve)
- draft → rejected (POST reject)
- approved → applied (POST apply, richiede write_products)
- approved → rejected (prima di apply)

## Vietato

- draft → applied (skip approve)
- generate → auto apply
- applied → draft (no rollback automatico in v1)

## SeoChangeLog

Ogni apply crea log con `applied_values`, `shopify_response`, `status`, `error_message`.
