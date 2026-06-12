import { Link } from "react-router-dom";
import type { ShopifyOfficialAnalytics } from "@gcr/shared";
import { APP_ROUTES } from "../../routes/config";

interface ShopifyOfficialUnavailablePanelProps {
  projectId: string;
  officialAnalytics: ShopifyOfficialAnalytics;
}

export function ShopifyOfficialUnavailablePanel({
  projectId,
  officialAnalytics,
}: ShopifyOfficialUnavailablePanelProps) {
  const warnings = officialAnalytics.dataQuality.warnings;
  const message = warnings[0] ?? "ShopifyQL non è disponibile per questo store.";

  return (
    <section className="shopify-official-unavailable gcr-card">
      <h2 className="shopify-panel__title">ShopifyQL non disponibile</h2>
      <p className="shopify-panel__context">{message}</p>
      <ul className="shopify-official-unavailable__reasons">
        <li>Lo scope OAuth `read_reports` potrebbe mancare sul token attuale.</li>
        <li>ShopifyQL richiede una nuova autorizzazione dell&apos;app Shopify.</li>
        <li>I permessi potrebbero non essere ancora approvati per questo store.</li>
      </ul>
      <Link to={APP_ROUTES.projectShopifyConnect(projectId)} className="gcr-btn gcr-btn--primary">
        Riconnetti Shopify
      </Link>
    </section>
  );
}
