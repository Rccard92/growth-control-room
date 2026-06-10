import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import {
  useShopifyDashboard,
  useShopifyOrders,
  useShopifyProducts,
  useShopifyStatus,
  useShopifySync,
} from "../hooks/useShopify";
import { APP_ROUTES } from "../routes/config";

function formatMoney(value: string, currency = "EUR"): string {
  const amount = Number(value);
  if (Number.isNaN(amount)) return value;
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(amount);
}

function formatDate(value?: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("it-IT");
}

export function ShopifyPage() {
  const { id } = useParams<{ id: string }>();
  const { data: status, isLoading: statusLoading, error: statusError } = useShopifyStatus(id);
  const connected = status?.connected ?? false;

  const { data: dashboard } = useShopifyDashboard(id, connected);
  const { data: products } = useShopifyProducts(id, connected);
  const { data: orders } = useShopifyOrders(id, connected);
  const syncMutation = useShopifySync(id!);

  if (statusLoading) {
    return <div className="gcr-skeleton" style={{ height: 200 }} />;
  }

  if (!connected) {
    return (
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
        <PageHeader
          title="Shopify Control Room"
          subtitle="Store, ordini, prodotti e inventario"
          breadcrumb={[
            { label: "Progetti", href: APP_ROUTES.projects },
            { label: id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
            { label: "Shopify" },
          ]}
        />
        <div className="gcr-card" style={{ maxWidth: 480 }}>
          <StatusBadge variant="not_connected" label="Shopify non collegato" />
          <h3 className="gcr-card__title" style={{ marginTop: "1rem" }}>
            Connetti il tuo store
          </h3>
          <p className="gcr-card__description">
            Collega Shopify con una Custom App e Admin API access token per sincronizzare ordini e prodotti.
          </p>
          <Link to={APP_ROUTES.projectShopifyConnect(id!)} className="gcr-btn gcr-btn--primary">
            Connetti Shopify
          </Link>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="Shopify Control Room"
        subtitle={
          status?.shopName
            ? `${status.shopName} · ${status.shopDomain ?? ""}`
            : "Store, ordini, prodotti e inventario"
        }
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Shopify" },
        ]}
        actions={
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            {syncMutation.isPending ? "Sincronizzazione…" : "Sincronizza dati"}
          </button>
        }
      />

      {(statusError || syncMutation.isError) && (
        <div className="gcr-alert gcr-alert--error" style={{ marginBottom: "1rem" }}>
          {statusError?.message ?? syncMutation.error?.message}
        </div>
      )}

      {syncMutation.isSuccess && (
        <div className="gcr-card" style={{ marginBottom: "1rem", borderColor: "rgba(52, 211, 153, 0.3)" }}>
          <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--gcr-success)" }}>
            Sync completato: {syncMutation.data.productsSynced} prodotti, {syncMutation.data.ordersSynced} ordini
          </p>
        </div>
      )}

      {dashboard && (
        <div className="gcr-grid gcr-grid--auto" style={{ marginBottom: "1.5rem" }}>
          <MetricCard label="Revenue" value={formatMoney(dashboard.revenue)} />
          <MetricCard label="Ordini" value={dashboard.ordersCount} />
          <MetricCard label="AOV" value={formatMoney(dashboard.averageOrderValue)} />
          <MetricCard label="Prodotti" value={dashboard.productsCount} />
          <MetricCard label="Ultimo sync" value={formatDate(dashboard.lastSyncAt)} />
        </div>
      )}

      <div style={{ display: "grid", gap: "1.5rem" }}>
        <div className="gcr-card">
          <h3 className="gcr-card__title">Ordini recenti</h3>
          {!orders?.length ? (
            <p style={{ color: "var(--gcr-text-muted)", fontSize: "0.875rem", margin: 0 }}>
              Nessun ordine. Esegui una sincronizzazione.
            </p>
          ) : (
            <table className="gcr-table">
              <thead>
                <tr>
                  <th>Ordine</th>
                  <th>Data</th>
                  <th>Stato</th>
                  <th style={{ textAlign: "right" }}>Totale</th>
                </tr>
              </thead>
              <tbody>
                {orders.slice(0, 10).map((order) => (
                  <tr key={order.id}>
                    <td>{order.orderName ?? order.shopifyGid}</td>
                    <td>{formatDate(order.createdAtShopify)}</td>
                    <td>{order.financialStatus ?? "—"}</td>
                    <td style={{ textAlign: "right" }}>
                      {formatMoney(order.totalPrice, order.currency ?? "EUR")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="gcr-card">
          <h3 className="gcr-card__title">Prodotti</h3>
          {!products?.length ? (
            <p style={{ color: "var(--gcr-text-muted)", fontSize: "0.875rem", margin: 0 }}>
              Nessun prodotto. Esegui una sincronizzazione.
            </p>
          ) : (
            <table className="gcr-table">
              <thead>
                <tr>
                  <th>Titolo</th>
                  <th>Stato</th>
                  <th style={{ textAlign: "right" }}>Inventario</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id}>
                    <td>{product.title}</td>
                    <td>{product.status ?? "—"}</td>
                    <td style={{ textAlign: "right" }}>{product.totalInventory ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {dashboard && dashboard.lowStockProducts.length > 0 && (
          <div className="gcr-card">
            <h3 className="gcr-card__title">Scorte basse</h3>
            <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.875rem", color: "var(--gcr-text-muted)" }}>
              {dashboard.lowStockProducts.map((product) => (
                <li key={product.id}>
                  {product.title} — {product.totalInventory ?? 0} pz
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </motion.div>
  );
}
