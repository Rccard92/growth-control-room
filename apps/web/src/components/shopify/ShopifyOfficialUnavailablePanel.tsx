import { Link } from "react-router-dom";
import type { ShopifyOfficialAnalytics } from "@gcr/shared";
import { APP_ROUTES } from "../../routes/config";

interface ShopifyOfficialUnavailablePanelProps {
  projectId: string;
  officialAnalytics: ShopifyOfficialAnalytics;
}

/** Hints shown only when the cause really is a missing OAuth scope. */
const SCOPE_HINTS = [
  "Lo scope OAuth read_reports potrebbe mancare sul token attuale.",
  "ShopifyQL richiede una nuova autorizzazione dell'app Shopify.",
  "I permessi potrebbero non essere ancora approvati per questo store.",
];

/** A missing scope is the only cause a reconnection can fix. */
function looksLikeMissingScope(message: string): boolean {
  const lowered = message.toLowerCase();
  return (
    lowered.includes("read_reports")
    || lowered.includes("non autorizzato")
    || lowered.includes("access denied")
  );
}

export function ShopifyOfficialUnavailablePanel({
  projectId,
  officialAnalytics,
}: ShopifyOfficialUnavailablePanelProps) {
  const warnings = officialAnalytics.dataQuality.warnings;
  const message = warnings[0] ?? "ShopifyQL non è disponibile per questo store.";
  const scopeIssue = looksLikeMissingScope(message);

  return (
    <section className="shopify-official-unavailable gcr-card">
      <h2 className="shopify-panel__title">ShopifyQL non disponibile</h2>
      <p className="shopify-panel__context">{message}</p>
      {scopeIssue ? (
        <>
          <ul className="shopify-official-unavailable__reasons">
            {SCOPE_HINTS.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
          <Link
            to={APP_ROUTES.projectShopifyConnect(projectId)}
            className="gcr-btn gcr-btn--primary"
          >
            Riconnetti Shopify
          </Link>
        </>
      ) : (
        <p className="shopify-panel__context">
          I dati di vendita restano disponibili dal calcolo locale sugli ordini
          sincronizzati. Riconnettere Shopify non risolve questo errore.
        </p>
      )}
    </section>
  );
}
