import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate, useParams } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { useShopifyConnect } from "../hooks/useShopify";
import { APP_ROUTES } from "../routes/config";

export function ShopifyConnectPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const connect = useShopifyConnect(id!);
  const [shopDomain, setShopDomain] = useState("");
  const [adminAccessToken, setAdminAccessToken] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await connect.mutateAsync({
      shopDomain: shopDomain.trim(),
      adminAccessToken: adminAccessToken.trim(),
    });
    navigate(APP_ROUTES.projectShopify(id!));
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="Connetti Shopify"
        subtitle="Custom App + Admin API access token"
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Integrazioni", href: id ? APP_ROUTES.projectIntegrations(id) : undefined },
          { label: "Connetti" },
        ]}
      />
      <div className="gcr-card" style={{ maxWidth: 480 }}>
        <p style={{ fontSize: "0.875rem", color: "var(--gcr-text-muted)", margin: "0 0 1.25rem", lineHeight: 1.6 }}>
          Usa una Custom App Shopify con permessi <code>read_products</code> e{" "}
          <code>read_orders</code>. Per il modulo blog serviranno anche{" "}
          <code>write_content</code> nello step successivo.
        </p>
        <form
          style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}
          onSubmit={handleSubmit}
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
          {connect.isError && (
            <div className="gcr-alert gcr-alert--error">{connect.error.message}</div>
          )}
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <button
              type="submit"
              className="gcr-btn gcr-btn--primary"
              disabled={connect.isPending}
            >
              {connect.isPending ? "Connessione…" : "Connetti store"}
            </button>
            <Link to={APP_ROUTES.projectIntegrations(id!)} className="gcr-btn gcr-btn--secondary">
              Annulla
            </Link>
          </div>
        </form>
      </div>
    </motion.div>
  );
}
