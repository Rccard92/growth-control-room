import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type {
  ShopifyDashboardReconciliation,
  ShopifyDashboardSummary,
  ShopifyOfficialAnalytics,
  ShopifyOrderDataCoverage,
} from "@gcr/shared";
import { ShopifyExecutiveStrip } from "./ShopifyExecutiveStrip";

const summary = {
  averageOrderValue: "0.00",
  activeProductsCount: 53,
  productsCount: 57,
  criticalAlertsCount: 5,
} as unknown as ShopifyDashboardSummary;

const reconciliation = {
  salesBreakdown: { totalSales: "0.00" },
  orders: { total: 0, paid: 0, pending: 0 },
} as unknown as ShopifyDashboardReconciliation;

const officialAnalytics = { available: false, kpis: {} } as unknown as ShopifyOfficialAnalytics;

function markup(orderDataCoverage?: ShopifyOrderDataCoverage): string {
  return renderToStaticMarkup(
    <ShopifyExecutiveStrip
      summary={summary}
      reconciliation={reconciliation}
      officialAnalytics={officialAnalytics}
      trackingQualityScore={0}
      formatMoney={(value) => `${value} €`}
      periodLabel="Ultimi 30 giorni"
      orderDataCoverage={orderDataCoverage}
    />,
  );
}

describe("ShopifyExecutiveStrip", () => {
  it("shows n/d instead of zero when the period has no synced data", () => {
    const html = markup({
      status: "uncovered",
      orderMetricsReliable: false,
      isStale: true,
      lastSyncAt: "2026-07-13T14:50:00Z",
      coveredUntil: null,
      message: "L'ultimo sync Shopify risale a 67 giorni fa.",
    });

    expect(html).toContain("n/d");
    expect(html).toContain("67 giorni fa");
    expect(html).toContain("Dati non sincronizzati");
    expect(html).toContain("shopify-coverage-banner--critical");
    // Counts that do not depend on orders stay visible.
    expect(html).toContain("53");
  });

  it("shows the real values when the period is covered", () => {
    const html = markup({
      status: "covered",
      orderMetricsReliable: true,
      isStale: false,
      lastSyncAt: "2026-09-19T10:00:00Z",
      coveredUntil: "2026-09-19T10:00:00Z",
      message: null,
    });

    expect(html).not.toContain("n/d");
    expect(html).toContain("0%");
    expect(html).not.toContain("shopify-coverage-banner");
  });

  it("stays backward compatible when the API sends no coverage block", () => {
    expect(markup(undefined)).not.toContain("n/d");
  });
});
