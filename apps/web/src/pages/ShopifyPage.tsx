import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { AttributionReadinessPanel } from "../components/shopify/AttributionReadinessPanel";
import { EcommerceDiagnosisPanel } from "../components/shopify/EcommerceDiagnosisPanel";
import { InventoryRiskPanel } from "../components/shopify/InventoryRiskPanel";
import { OrdersOperationsPanel } from "../components/shopify/OrdersOperationsPanel";
import { ProductIntelligencePanel } from "../components/shopify/ProductIntelligencePanel";
import { SeoOpportunitiesPanel } from "../components/shopify/SeoOpportunitiesPanel";
import { ShopifyAlertCenter } from "../components/shopify/ShopifyAlertCenter";
import { ShopifyExecutiveStrip } from "../components/shopify/ShopifyExecutiveStrip";
import { ShopifyStatusBadge } from "../components/shopify/ShopifyStatusBadge";
import { useShopifyDashboard, useShopifyStatus, useShopifySync } from "../hooks/useShopify";
import { queryKeys } from "../lib/queryKeys";
import { APP_ROUTES } from "../routes/config";

const SHOPIFY_ERROR_MESSAGES: Record<string, string> = {
  invalid_state: "Sessione OAuth scaduta o non valida. Riprova la connessione.",
  hmac_invalid: "Verifica di sicurezza Shopify non riuscita. Riprova.",
  token_exchange_failed: "Shopify non ha accettato l'autorizzazione. Riprova.",
  shopify_unavailable: "Shopify non è raggiungibile al momento. Riprova più tardi.",
  connection_failed: "Impossibile completare la connessione. Riprova.",
  oauth_not_configured: "OAuth Shopify non configurato sul server. Contatta l'amministratore.",
  missing_params: "Parametri OAuth mancanti. Riprova la connessione.",
};

function formatMoney(value: string, currency?: string | null): string {
  const amount = Number(value);
  if (Number.isNaN(amount)) return value;
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: currency ?? "EUR",
    maximumFractionDigits: 2,
  }).format(amount);
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
  const {
    data: dashboard,
    isLoading: dashboardLoading,
    error: dashboardError,
  } = useShopifyDashboard(id, connected);
  const syncMutation = useShopifySync(id!);

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

  if (statusLoading) {
    return (
      <div className="shopify-dashboard">
        <div className="shopify-skeleton-grid">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="gcr-skeleton shopify-skeleton-card" />
          ))}
        </div>
      </div>
    );
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
        {oauthBanner &&
          (oauthBanner.type === "success" ? (
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
          ))}
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

  const summary = dashboard?.summary;

  return (
    <motion.div
      className="shopify-dashboard"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="shopify-dashboard__header">
        <PageHeader
          title="Shopify Control Room"
          subtitle={summary?.shopDomain ?? status?.shopDomain ?? "E-commerce Control Room"}
          breadcrumb={[
            { label: "Progetti", href: APP_ROUTES.projects },
            { label: id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
            { label: "Shopify" },
          ]}
        />
        <div className="shopify-dashboard__header-actions">
          <ShopifyStatusBadge connected={connected} summary={summary} />
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            {syncMutation.isPending ? "Sincronizzazione…" : "Sincronizza dati"}
          </button>
        </div>
      </div>

      {oauthBanner &&
        (oauthBanner.type === "success" ? (
          <div className="gcr-card" style={{ borderColor: "rgba(52, 211, 153, 0.3)" }}>
            <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--gcr-success)" }}>
              {oauthBanner.message}
            </p>
          </div>
        ) : (
          <div className="gcr-alert gcr-alert--error">{oauthBanner.message}</div>
        ))}

      {(statusError || dashboardError || syncMutation.isError) && (
        <div className="gcr-alert gcr-alert--error">
          {statusError?.message ?? dashboardError?.message ?? syncMutation.error?.message}
        </div>
      )}

      {syncMutation.isSuccess && (
        <div className="gcr-card" style={{ borderColor: "rgba(52, 211, 153, 0.3)" }}>
          <p style={{ margin: 0, fontSize: "0.8125rem", color: "var(--gcr-success)" }}>
            Sync completato: {syncMutation.data.productsSynced} prodotti,{" "}
            {syncMutation.data.ordersSynced} ordini
          </p>
        </div>
      )}

      {dashboardLoading && (
        <div className="shopify-skeleton-grid">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="gcr-skeleton shopify-skeleton-card" />
          ))}
        </div>
      )}

      {!dashboardLoading && dashboard && summary && (
        <>
          <ShopifyExecutiveStrip summary={summary} formatMoney={formatMoney} />

          <EcommerceDiagnosisPanel items={dashboard.dailyDiagnosis} />

          <div className="shopify-dashboard__layout">
            <div className="shopify-dashboard__main">
              <ProductIntelligencePanel
                performance={dashboard.productPerformance}
                formatMoney={formatMoney}
              />
              <InventoryRiskPanel inventory={dashboard.inventory} />
              <OrdersOperationsPanel orders={dashboard.orders} formatMoney={formatMoney} />
              <SeoOpportunitiesPanel seo={dashboard.seo} />
            </div>

            <div className="shopify-dashboard__side">
              <ShopifyAlertCenter alerts={dashboard.alerts} />
              <AttributionReadinessPanel
                attribution={dashboard.attribution}
                shopifyConnected={connected}
              />
            </div>
          </div>
        </>
      )}

      {!dashboardLoading && !dashboard && (
        <div className="gcr-card">
          <p className="shopify-empty-copy">
            Nessun dato dashboard disponibile. Esegui una sincronizzazione per popolare la Control
            Room.
          </p>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            style={{ marginTop: "1rem" }}
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            Sincronizza dati
          </button>
        </div>
      )}
    </motion.div>
  );
}
