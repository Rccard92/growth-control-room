import { StatusBadge } from "../StatusBadge";
import type { ShopifyDashboardSummary } from "@gcr/shared";

interface ShopifyStatusBadgeProps {
  connected: boolean;
  summary?: ShopifyDashboardSummary;
}

function formatSyncDate(value?: string | null): string {
  if (!value) return "Mai sincronizzato";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Data non disponibile";
  return new Intl.DateTimeFormat("it-IT", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function ShopifyStatusBadge({ connected, summary }: ShopifyStatusBadgeProps) {
  return (
    <div className="shopify-status-badge">
      <StatusBadge
        variant={connected ? "connected" : "not_connected"}
        label={connected ? "Shopify connesso" : "Non connesso"}
      />
      {connected && (
        <span className="shopify-status-badge__meta">
          Ultimo sync: {formatSyncDate(summary?.lastSyncAt)}
        </span>
      )}
    </div>
  );
}
