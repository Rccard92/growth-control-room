import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate, useParams } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { useShopifyConnect, useShopifyOAuthStart } from "../hooks/useShopify";
import { APP_ROUTES } from "../routes/config";

export function ShopifyConnectPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const oauthStart = useShopifyOAuthStart(id!);
  const manualConnect = useShopifyConnect(id!);
  const [shopDomain, setShopDomain] = useState("");
  const [adminAccessToken, setAdminAccessToken] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  async function handleOAuthSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await oauthStart.mutateAsync(shopDomain.trim());
  }

  async function handleManualSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await manualConnect.mutateAsync({
      shopDomain: shopDomain.trim(),
      adminAccessToken: adminAccessToken.trim(),
    });
    navigate(APP_ROUTES.projectShopify(id!));
  }

  const activeError = oauthStart.error ?? manualConnect.error;
  const isPending = oauthStart.isPending || manualConnect.isPending;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="Connetti Shopify"
        subtitle="Autorizza Growth Control Room sul tuo store"
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Integrazioni", href: id ? APP_ROUTES.projectIntegrations(id) : undefined },
          { label: "Connetti" },
        ]}
      />
      <div className="gcr-card" style={{ maxWidth: 480 }}>
        <p style={{ fontSize: "0.875rem", color: "var(--gcr-text-muted)", margin: "0 0 1.25rem", lineHeight: 1.6 }}>
          Verrai reindirizzato su Shopify per autorizzare Growth Control Room. Non dovrai copiare token manualmente.
        </p>
        <form
          style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}
          onSubmit={handleOAuthSubmit}
        >
          <div className="gcr-field">
            <label htmlFor="shop_domain">Dominio shop</label>
            <input
              id="shop_domain"
              type="text"
              placeholder="nomesito.myshopify.com"
              value={shopDomain}
              onChange={(e) => setShopDomain(e.target.value)}
              required
            />
          </div>
          {activeError && (
            <div className="gcr-alert gcr-alert--error">{activeError.message}</div>
          )}
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <button
              type="submit"
              className="gcr-btn gcr-btn--primary"
              disabled={isPending}
            >
              {oauthStart.isPending ? "Reindirizzamento…" : "Connetti Shopify"}
            </button>
            <Link to={APP_ROUTES.projectIntegrations(id!)} className="gcr-btn gcr-btn--secondary">
              Annulla
            </Link>
          </div>
        </form>

        <div style={{ marginTop: "1.5rem", borderTop: "1px solid var(--gcr-border)", paddingTop: "1rem" }}>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            style={{ fontSize: "0.8125rem" }}
            onClick={() => setShowAdvanced((value) => !value)}
          >
            {showAdvanced ? "Nascondi connessione avanzata" : "Connessione avanzata (token manuale)"}
          </button>
          {showAdvanced && (
            <form
              style={{ display: "flex", flexDirection: "column", gap: "1.25rem", marginTop: "1rem" }}
              onSubmit={handleManualSubmit}
            >
              <p style={{ fontSize: "0.8125rem", color: "var(--gcr-text-muted)", margin: 0, lineHeight: 1.6 }}>
                Solo per sviluppo o casi eccezionali: usa una Custom App Shopify con Admin API access token.
              </p>
              <div className="gcr-field">
                <label htmlFor="admin_access_token">Admin API access token</label>
                <input
                  id="admin_access_token"
                  type="password"
                  placeholder="shpat_..."
                  value={adminAccessToken}
                  onChange={(e) => setAdminAccessToken(e.target.value)}
                  required
                />
              </div>
              <button
                type="submit"
                className="gcr-btn gcr-btn--secondary"
                disabled={manualConnect.isPending}
              >
                {manualConnect.isPending ? "Connessione…" : "Connetti con token manuale"}
              </button>
            </form>
          )}
        </div>
      </div>
    </motion.div>
  );
}
