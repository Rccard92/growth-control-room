import type { ReactNode } from "react";
import type { DateRangeParams } from "@gcr/shared";
import { DateRangeSelector } from "../DateRangeSelector";
import { PageHeader } from "../PageHeader";
import { ShopifyStatusBadge } from "./ShopifyStatusBadge";
import type { ShopifyDashboardSummary, ShopifyStatus } from "@gcr/shared";
import { APP_ROUTES } from "../../routes/config";

interface ShopifyControlRoomHeaderProps {
  projectId: string;
  shopDomain?: string | null;
  connected: boolean;
  summary?: ShopifyDashboardSummary;
  status?: ShopifyStatus;
  syncing: boolean;
  onSync: () => void;
  syncSummary?: ReactNode;
  dateRange: DateRangeParams;
  onDateRangeChange: (value: DateRangeParams) => void;
  periodLabel?: string;
}

export function ShopifyControlRoomHeader({
  projectId,
  shopDomain,
  connected,
  summary,
  status,
  syncing,
  onSync,
  syncSummary,
  dateRange,
  onDateRangeChange,
  periodLabel,
}: ShopifyControlRoomHeaderProps) {
  const domain = summary?.shopDomain ?? shopDomain ?? status?.shopDomain ?? "E-commerce Control Room";

  return (
    <header className="shopify-control-room-header">
      <div className="shopify-control-room-header__main">
        <PageHeader
          title="Shopify Control Room"
          subtitle={domain}
          breadcrumb={[
            { label: "Progetti", href: APP_ROUTES.projects },
            { label: projectId, href: APP_ROUTES.project(projectId) },
            { label: "Shopify" },
          ]}
        />
        <div className="shopify-control-room-header__actions">
          {periodLabel && (
            <p className="shopify-period-banner__performance">
              Performance: <span>{periodLabel}</span>
            </p>
          )}
          <DateRangeSelector
            value={dateRange}
            onChange={onDateRangeChange}
            disabled={syncing}
          />
          <ShopifyStatusBadge connected={connected} summary={summary} />
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            onClick={onSync}
            disabled={syncing}
          >
            {syncing ? "Sincronizzazione…" : "Sincronizza dati"}
          </button>
        </div>
      </div>
      {syncSummary}
    </header>
  );
}
