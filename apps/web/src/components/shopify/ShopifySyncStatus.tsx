import type { ShopifyDashboardSummary } from "@gcr/shared";

interface ShopifySyncStatusProps {
  connected: boolean;
  summary?: ShopifyDashboardSummary | null;
}

function formatDate(value?: string | null): string {
  if (!value) return "Mai sincronizzato";
  return new Date(value).toLocaleString("it-IT");
}

export function ShopifySyncStatus({ connected, summary }: ShopifySyncStatusProps) {
  return (
    <div className="shopify-sync-status">
      <span className={`shopify-badge shopify-badge--${connected ? "connected" : "offline"}`}>
        {connected ? "Connesso" : "Offline"}
      </span>
      <span className="shopify-sync-status__meta">
        {summary?.shopDomain ?? "—"} · Ultimo sync: {formatDate(summary?.lastSyncAt)}
      </span>
    </div>
  );
}
