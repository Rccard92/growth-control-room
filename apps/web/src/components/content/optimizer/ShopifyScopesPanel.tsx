import type { ShopifyScopesResponse } from "@gcr/shared";
import { startShopifyOAuth } from "../../../lib/shopify-api";

interface ShopifyScopesPanelProps {
  scopes?: ShopifyScopesResponse;
  loading?: boolean;
  shopDomain?: string | null;
  onRefresh?: () => void;
  compact?: boolean;
}

export function ShopifyScopesPanel({
  scopes,
  loading,
  shopDomain,
  onRefresh,
  compact = false,
}: ShopifyScopesPanelProps) {
  const handleReconnect = async () => {
    if (!shopDomain) return;
    const projectMatch = window.location.pathname.match(/\/projects\/([^/]+)/);
    const projectId = projectMatch?.[1];
    if (!projectId) return;
    const result = await startShopifyOAuth(projectId, shopDomain);
    window.location.href = result.authorizationUrl;
  };

  if (loading && !scopes) {
    return (
      <div className="shopify-scopes-panel">
        <p className="shopify-scopes-panel__title">Shopify Permission Check</p>
        <p className="shopify-scopes-panel__row">Verifica permessi in corso…</p>
      </div>
    );
  }

  if (!scopes) return null;

  const panelClass = scopes.canWriteProducts
    ? "shopify-scopes-panel shopify-scopes-panel--ok"
    : "shopify-scopes-panel";

  return (
    <div className={panelClass}>
      <p className="shopify-scopes-panel__title">Shopify Permission Check</p>
      {!compact && (
        <>
          <p className="shopify-scopes-panel__row">
            <strong>Configured scopes:</strong> {scopes.configuredScopes.join(", ") || "—"}
          </p>
          <p className="shopify-scopes-panel__row">
            <strong>Granted scopes:</strong> {scopes.grantedScopes.join(", ") || "—"}
          </p>
          <p className="shopify-scopes-panel__row">
            <strong>Missing scopes:</strong> {scopes.missingScopes.join(", ") || "—"}
          </p>
        </>
      )}
      <p className="shopify-scopes-panel__row">
        <strong>write_products autorizzato:</strong> {scopes.canWriteProducts ? "sì" : "no"}
      </p>
      <p className="shopify-scopes-panel__message">{scopes.message}</p>
      <div className="shopify-scopes-panel__actions">
        {onRefresh && (
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            disabled={loading}
            onClick={onRefresh}
          >
            {loading ? "Verifica…" : "Verifica permessi Shopify"}
          </button>
        )}
        {scopes.requiresReconnect && shopDomain && (
          <button
            type="button"
            className="gcr-btn gcr-btn--primary gcr-btn--sm"
            onClick={() => void handleReconnect()}
          >
            Riconnetti Shopify
          </button>
        )}
      </div>
    </div>
  );
}
