import { FormEvent, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Button, Card, PageHeader } from "@gcr/ui";
import { connectShopify } from "../lib/shopify-api";

export function ShopifyConnectPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [shopDomain, setShopDomain] = useState("");
  const [adminAccessToken, setAdminAccessToken] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!id) return;

    setSubmitting(true);
    setError(null);

    try {
      await connectShopify(id, {
        shopDomain: shopDomain.trim(),
        adminAccessToken: adminAccessToken.trim(),
      });
      navigate(`/projects/${id}/shopify`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connessione fallita");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Connetti Shopify"
        subtitle="Collega lo store con una Custom App e Admin API access token"
        breadcrumb={[
          { label: "Progetti", href: "/projects" },
          { label: id ?? "", href: `/projects/${id}` },
          { label: "Integrazioni", href: `/projects/${id}/integrations` },
          { label: "Connetti Shopify" },
        ]}
      />
      <Card title="Credenziali store">
        <p style={{ fontSize: "0.875rem", color: "#6b7280", margin: "0 0 1rem" }}>
          Usa una Custom App Shopify con permessi <code>read_products</code> e{" "}
          <code>read_orders</code>. Per il modulo blog serviranno anche i permessi{" "}
          <code>write_content</code> nello step successivo.
        </p>
        <form
          style={{ display: "flex", flexDirection: "column", gap: "1rem", maxWidth: "28rem" }}
          onSubmit={handleSubmit}
        >
          <div className="login-page__field">
            <label htmlFor="shop_domain">Dominio shop</label>
            <input
              id="shop_domain"
              type="text"
              placeholder="nomesito.myshopify.com"
              value={shopDomain}
              onChange={(event) => setShopDomain(event.target.value)}
              required
            />
          </div>
          <div className="login-page__field">
            <label htmlFor="admin_access_token">Admin API access token</label>
            <input
              id="admin_access_token"
              type="password"
              placeholder="shpat_..."
              value={adminAccessToken}
              onChange={(event) => setAdminAccessToken(event.target.value)}
              required
            />
          </div>
          {error && (
            <p style={{ color: "#dc2626", fontSize: "0.875rem", margin: 0 }}>{error}</p>
          )}
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Connessione…" : "Connetti store"}
            </Button>
            <Link to={`/projects/${id}/integrations`}>
              <Button variant="secondary" type="button">
                Annulla
              </Button>
            </Link>
          </div>
        </form>
      </Card>
    </>
  );
}
