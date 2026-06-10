import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
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
import { queryKeys } from "../lib/queryKeys";
import { APP_ROUTES } from "../routes/config";

const SHOPIFY_ERROR_MESSAGES: Record<string, string> = {
  invalid_state: "Sessione OAuth scaduta o non valida. Riprova la connessione.",
  hmac_invalid: "Verifica di sicurezza Shopify non riuscita. Riprova.",
  invalid_shop: "Dominio shop non valido. Usa il formato nomesito.myshopify.com.",
  token_exchange_failed: "Shopify non ha accettato l'autorizzazione. Riprova.",
  shopify_unavailable: "Shopify non è raggiungibile al momento. Riprova più tardi.",
  connection_failed: "Impossibile completare la connessione. Riprova.",
  oauth_not_configured: "OAuth Shopify non configurato sul server. Contatta l'amministratore.",
  missing_params: "Parametri OAuth mancanti. Riprova la connessione.",
};

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
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const [oauthBanner, setOauthBanner] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);
  const { data: status, isLoading: statusLoading, error: statusError } = useShopifyStatus(id);
  const connected = status?.connected ?? false;

  useEffect(() => {
    const connectedParam = searchParams.get("shopify_connected");
    const errorParam = searchParams.get("shopify_error");

    if (connectedParam === "1") {
      setOauthBanner({
        type: "success",
        message: "Shopify collegato con successo.",
      });
      void queryClient.invalidateQueries({ queryKey: queryKeys.shopify.status(id ?? "") });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.integrations(id ?? ""),
      });
    } else if (errorParam) {
      setOauthBanner({
        type: "error",
        message:
          SHOPIFY_ERROR_MESSAGES[errorParam] ??
          "Errore durante la connessione Shopify. Riprova.",
      });
    }

    if (connectedParam || errorParam) {
      setSearchParams({}, { replace: true });
    }
  }, [id, queryClient, searchParams, setSearchParams]);

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
        {oauthBanner && (
          oauthBanner.type === "success" ? (
            <div
              className="gcr-card"
              style={{ marginBottom: "1rem", maxWidth: 480, borderColor: "rgba(52, 211, 153, 0.3)" }}
            >
              <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--gcr-success)" }}>
                {oauthBanner.message}
              </p>
            </div>
          ) : (
            <div className="gcr-alert gcr-alert--error" style={{ marginBottom: "1rem", maxWidth: 480 }}>
              {oauthBanner.message}
            </div>
          )
        )}
        <div className="gcr-card" style={{ maxWidth: 480 }}>
          <StatusBadge variant="not_connected" label="Shopify non collegato" />
          <h3 className="gcr-card__title" style={{ marginTop: "1rem" }}>
            Connetti il tuo store
          </h3>
          <p className="gcr-card__description">
            Autorizza Growth Control Room su Shopify per sincronizzare ordini e prodotti in modo sicuro.
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

      {oauthBanner && (
        oauthBanner.type === "success" ? (
          <div
            className="gcr-card"
            style={{ marginBottom: "1rem", borderColor: "rgba(52, 211, 153, 0.3)" }}
          >
            <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--gcr-success)" }}>
              {oauthBanner.message}
            </p>
          </div>
        ) : (
          <div className="gcr-alert gcr-alert--error" style={{ marginBottom: "1rem" }}>
            {oauthBanner.message}
          </div>
        )
      )}

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
