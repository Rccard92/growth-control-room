import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import type { ShopifyDashboard, ShopifyOrder, ShopifyProduct } from "@gcr/shared";
import { Button, Card, PageHeader } from "@gcr/ui";
import {
  getShopifyDashboard,
  getShopifyOrders,
  getShopifyProducts,
  getShopifyStatus,
  syncShopify,
} from "../lib/shopify-api";

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
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const [dashboard, setDashboard] = useState<ShopifyDashboard | null>(null);
  const [products, setProducts] = useState<ShopifyProduct[]>([]);
  const [orders, setOrders] = useState<ShopifyOrder[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [shopName, setShopName] = useState<string | null>(null);
  const [shopDomain, setShopDomain] = useState<string | null>(null);

  async function loadData(projectId: string) {
    setLoading(true);
    setError(null);

    try {
      const status = await getShopifyStatus(projectId);
      if (!status.connected) {
        setConnected(false);
        return;
      }

      setConnected(true);
      setShopName(status.shopName ?? null);
      setShopDomain(status.shopDomain ?? null);

      const [dashboardData, productsData, ordersData] = await Promise.all([
        getShopifyDashboard(projectId),
        getShopifyProducts(projectId),
        getShopifyOrders(projectId),
      ]);
      setDashboard(dashboardData);
      setProducts(productsData);
      setOrders(ordersData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore nel caricamento");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!id) return;
    void loadData(id);
  }, [id]);

  async function handleSync() {
    if (!id) return;
    setSyncing(true);
    setError(null);
    try {
      await syncShopify(id);
      await loadData(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sincronizzazione fallita");
    } finally {
      setSyncing(false);
    }
  }

  if (!loading && !connected && !error) {
    return <Navigate to={`/projects/${id}/shopify/connect`} replace />;
  }

  return (
    <>
      <PageHeader
        title="Shopify"
        subtitle={
          shopName
            ? `${shopName} (${shopDomain ?? ""})`
            : "Store, ordini, prodotti e inventario"
        }
        breadcrumb={[
          { label: "Progetti", href: "/projects" },
          { label: id ?? "", href: `/projects/${id}` },
          { label: "Shopify" },
        ]}
        actions={
          connected ? (
            <Button onClick={handleSync} disabled={syncing}>
              {syncing ? "Sincronizzazione…" : "Sincronizza dati Shopify"}
            </Button>
          ) : undefined
        }
      />

      {loading && (
        <p style={{ color: "#6b7280", fontSize: "0.875rem" }}>Caricamento Shopify…</p>
      )}
      {error && (
        <p style={{ color: "#dc2626", fontSize: "0.875rem" }}>{error}</p>
      )}

      {connected && dashboard && (
        <>
          <div className="placeholder-grid" style={{ marginBottom: "1.5rem" }}>
            <Card title="Fatturato" description="Periodo disponibile">
              <p style={{ fontSize: "1.5rem", fontWeight: 600, margin: 0 }}>
                {formatMoney(dashboard.revenue)}
              </p>
            </Card>
            <Card title="Ordini" description="Totale sincronizzati">
              <p style={{ fontSize: "1.5rem", fontWeight: 600, margin: 0 }}>
                {dashboard.ordersCount}
              </p>
            </Card>
            <Card title="AOV" description="Valore medio ordine">
              <p style={{ fontSize: "1.5rem", fontWeight: 600, margin: 0 }}>
                {formatMoney(dashboard.averageOrderValue)}
              </p>
            </Card>
            <Card title="Prodotti" description="Catalogo sincronizzato">
              <p style={{ fontSize: "1.5rem", fontWeight: 600, margin: 0 }}>
                {dashboard.productsCount}
              </p>
            </Card>
            <Card title="Ultimo sync" description="Timestamp">
              <p style={{ fontSize: "0.875rem", margin: 0 }}>
                {formatDate(dashboard.lastSyncAt)}
              </p>
            </Card>
          </div>

          <div style={{ display: "grid", gap: "1.5rem" }}>
            <Card title="Ordini recenti" description="Ultimi ordini sincronizzati">
              {orders.length === 0 ? (
                <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: 0 }}>
                  Nessun ordine. Esegui una sincronizzazione.
                </p>
              ) : (
                <table style={{ width: "100%", fontSize: "0.875rem", borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: "left", padding: "0.5rem 0" }}>Ordine</th>
                      <th style={{ textAlign: "left" }}>Data</th>
                      <th style={{ textAlign: "left" }}>Stato</th>
                      <th style={{ textAlign: "right" }}>Totale</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.slice(0, 10).map((order) => (
                      <tr key={order.id}>
                        <td style={{ padding: "0.5rem 0" }}>{order.orderName ?? order.shopifyGid}</td>
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
            </Card>

            <Card title="Prodotti" description="Catalogo sincronizzato">
              {products.length === 0 ? (
                <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: 0 }}>
                  Nessun prodotto. Esegui una sincronizzazione.
                </p>
              ) : (
                <table style={{ width: "100%", fontSize: "0.875rem", borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: "left", padding: "0.5rem 0" }}>Titolo</th>
                      <th style={{ textAlign: "left" }}>Stato</th>
                      <th style={{ textAlign: "right" }}>Inventario</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map((product) => (
                      <tr key={product.id}>
                        <td style={{ padding: "0.5rem 0" }}>{product.title}</td>
                        <td>{product.status ?? "—"}</td>
                        <td style={{ textAlign: "right" }}>
                          {product.totalInventory ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Card>

            {dashboard.lowStockProducts.length > 0 && (
              <Card title="Scorte basse" description="Prodotti con inventario ≤ 5">
                <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.875rem" }}>
                  {dashboard.lowStockProducts.map((product) => (
                    <li key={product.id}>
                      {product.title} — {product.totalInventory ?? 0} pz
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </div>
        </>
      )}

      {!connected && !loading && (
        <Card title="Shopify non connesso">
          <p style={{ margin: "0 0 1rem", fontSize: "0.875rem", color: "#6b7280" }}>
            Collega lo store per visualizzare ordini, prodotti e metriche.
          </p>
          <Link to={`/projects/${id}/shopify/connect`}>
            <Button>Connetti Shopify</Button>
          </Link>
        </Card>
      )}
    </>
  );
}
