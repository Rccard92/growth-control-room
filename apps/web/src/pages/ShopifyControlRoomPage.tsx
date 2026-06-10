import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { DailyDiagnosisPanel } from "../components/shopify/EcommerceDiagnosisPanel";
import { InventoryRiskPanel } from "../components/shopify/InventoryRiskPanel";
import { OrdersOperationsPanel } from "../components/shopify/OrdersOperationsPanel";
import { ProductIntelligencePanel } from "../components/shopify/ProductIntelligencePanel";
import { SeoOpportunitiesPanel } from "../components/shopify/SeoOpportunitiesPanel";
import { ShopifyAlertCenter } from "../components/shopify/ShopifyAlertCenter";
import { ShopifyAttributionIntelligencePanel } from "../components/shopify/ShopifyAttributionIntelligencePanel";
import { ShopifyControlRoomHeader } from "../components/shopify/ShopifyControlRoomHeader";
import { ShopifyExecutiveStrip } from "../components/shopify/ShopifyExecutiveStrip";
import { ShopifySyncSummary } from "../components/shopify/ShopifySyncSummary";
import { TrendIntelligencePanel } from "../components/shopify/TrendIntelligencePanel";
import { useShopifyDashboard, useShopifyStatus, useShopifySync } from "../hooks/useShopify";
import { useDateRangeParams } from "../hooks/useDateRangeParams";
import { getDateRangeDisplayLabel } from "../lib/date-range";
import { resolveShopifyDashboardBlocks } from "../lib/shopify-dashboard-blocks";
import { formatShopifyMoney } from "../lib/shopify-format";
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

function DashboardSkeleton() {
  return (
    <div className="shopify-skeleton-grid">
      {Array.from({ length: 8 }).map((_, index) => (
        <div key={index} className="gcr-skeleton shopify-skeleton-card" />
      ))}
    </div>
  );
}

export function ShopifyControlRoomPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const [oauthBanner, setOauthBanner] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const { dateRange, setDateRange } = useDateRangeParams();
  const { data: status, isLoading: statusLoading, error: statusError } = useShopifyStatus(id);
  const connected = status?.connected ?? false;
  const {
    data: dashboard,
    isLoading: dashboardLoading,
    error: dashboardError,
  } = useShopifyDashboard(id, connected, dateRange);
  const syncMutation = useShopifySync(projectId);

  useEffect(() => {
    const connectedParam = searchParams.get("shopify_connected");
    const errorParam = searchParams.get("shopify_error");

    if (connectedParam === "1") {
      setOauthBanner({
        type: "success",
        message: "Shopify collegato con successo.",
      });
      void queryClient.invalidateQueries({ queryKey: queryKeys.shopify.status(projectId) });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.projects.integrations(projectId),
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
      const next = new URLSearchParams(searchParams);
      next.delete("shopify_connected");
      next.delete("shopify_error");
      setSearchParams(next, { replace: true });
    }
  }, [projectId, queryClient, searchParams, setSearchParams]);

  if (statusLoading) {
    return (
      <div className="shopify-control-room shopify-dashboard">
        <DashboardSkeleton />
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
            { label: projectId, href: projectId ? APP_ROUTES.project(projectId) : undefined },
            { label: "Shopify" },
          ]}
        />
        {oauthBanner &&
          (oauthBanner.type === "success" ? (
            <div className="gcr-card shopify-oauth-banner shopify-oauth-banner--success">
              <p>{oauthBanner.message}</p>
            </div>
          ) : (
            <div className="gcr-alert gcr-alert--error shopify-oauth-banner">{oauthBanner.message}</div>
          ))}
        <div className="gcr-card" style={{ maxWidth: 480 }}>
          <StatusBadge variant="not_connected" label="Shopify non collegato" />
          <h3 className="gcr-card__title" style={{ marginTop: "1rem" }}>
            Connetti il tuo store
          </h3>
          <p className="gcr-card__description">
            Autorizza Growth Control Room su Shopify per sincronizzare ordini e prodotti in modo sicuro.
          </p>
          <Link to={APP_ROUTES.projectShopifyConnect(projectId)} className="gcr-btn gcr-btn--primary">
            Connetti Shopify
          </Link>
        </div>
      </motion.div>
    );
  }

  const blocks = dashboard ? resolveShopifyDashboardBlocks(dashboard) : null;
  const summary = blocks?.summary;
  const periodLabel = dashboard
    ? getDateRangeDisplayLabel(dateRange, dashboard.period.label)
    : getDateRangeDisplayLabel(dateRange);

  return (
    <motion.div
      className="shopify-control-room shopify-dashboard"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <ShopifyControlRoomHeader
        projectId={projectId}
        shopDomain={status?.shopDomain}
        connected={connected}
        summary={summary}
        status={status}
        syncing={syncMutation.isPending}
        onSync={() => syncMutation.mutate()}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        periodLabel={periodLabel}
        syncSummary={
          syncMutation.isSuccess && syncMutation.data ? (
            <ShopifySyncSummary data={syncMutation.data} />
          ) : undefined
        }
      />

      {oauthBanner &&
        (oauthBanner.type === "success" ? (
          <div className="gcr-card shopify-oauth-banner shopify-oauth-banner--success">
            <p>{oauthBanner.message}</p>
          </div>
        ) : (
          <div className="gcr-alert gcr-alert--error shopify-oauth-banner">{oauthBanner.message}</div>
        ))}

      {(statusError || dashboardError) && (
        <div className="gcr-alert gcr-alert--error">
          {statusError?.message ?? dashboardError?.message}
        </div>
      )}

      {syncMutation.isError && (
        <div className="gcr-alert gcr-alert--error">{syncMutation.error.message}</div>
      )}

      {dashboardLoading && <DashboardSkeleton />}

      {!dashboardLoading && dashboard && blocks && summary && (
        <div className="shopify-control-room__sections">
          <ShopifyExecutiveStrip
            summary={summary}
            trackingQualityScore={blocks.attributionIntelligence.trackingQualityScore}
            formatMoney={(value) => formatShopifyMoney(value, "EUR")}
            periodLabel={periodLabel}
            comparison={blocks.comparison}
          />

          <TrendIntelligencePanel comparison={blocks.comparison} />

          <DailyDiagnosisPanel items={blocks.dailyDiagnosis} />

          <ShopifyAlertCenter alerts={blocks.alerts} />

          <ShopifyAttributionIntelligencePanel
            intelligence={blocks.attributionIntelligence}
            availability={blocks.marketingReportAvailability}
            formatMoney={formatShopifyMoney}
            periodLabel={periodLabel}
            comparison={blocks.comparison}
          />

          <ProductIntelligencePanel
            productIntelligence={blocks.productIntelligence}
            formatMoney={(value) => formatShopifyMoney(value, "EUR")}
            periodLabel={periodLabel}
            comparison={blocks.comparison}
          />

          <InventoryRiskPanel inventoryRisk={blocks.inventoryRisk} />

          <OrdersOperationsPanel
            orderOperations={blocks.orderOperations}
            formatMoney={formatShopifyMoney}
            periodLabel={periodLabel}
          />

          <SeoOpportunitiesPanel seoOpportunities={blocks.seoOpportunities} />
        </div>
      )}

      {!dashboardLoading && !dashboard && (
        <div className="gcr-card shopify-empty-dashboard">
          <h3 className="gcr-card__title">Dashboard vuota</h3>
          <p className="shopify-empty-copy">
            Nessun dato operativo disponibile. Sincronizza lo store per popolare prodotti, ordini,
            inventario e attribution dalla Control Room.
          </p>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            {syncMutation.isPending ? "Sincronizzazione…" : "Sincronizza dati"}
          </button>
        </div>
      )}
    </motion.div>
  );
}
