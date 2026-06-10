import { useState } from "react";
import type {
  ShopifyAttributionIntelligence,
  ShopifyMarketingReportAvailability,
} from "@gcr/shared";
import { SHOPIFY_TABLE_ROW_LIMIT, sliceWithLimit } from "../../lib/shopify-dashboard-blocks";
import { ShowMoreToggle } from "./ShowMoreToggle";

interface ShopifyAttributionIntelligencePanelProps {
  intelligence: ShopifyAttributionIntelligence;
  availability: ShopifyMarketingReportAvailability;
  formatMoney: (value: string, currency?: string | null) => string;
}

function sourceChipClass(source: string): string {
  const normalized = source.toLowerCase();
  if (normalized.includes("email") || normalized.includes("klaviyo")) return "shopify-source-chip--email";
  if (
    normalized.includes("social") ||
    normalized.includes("facebook") ||
    normalized.includes("instagram") ||
    normalized.includes("meta")
  ) {
    return "shopify-source-chip--social";
  }
  if (normalized.includes("google") || normalized.includes("search")) return "shopify-source-chip--search";
  if (normalized === "direct") return "shopify-source-chip--direct";
  return "";
}

function AttributionTable({
  rows,
  formatMoney,
  valueKey,
  labelKey,
}: {
  rows: ShopifyAttributionIntelligence["revenueBySource"];
  formatMoney: (value: string, currency?: string | null) => string;
  valueKey: "source" | "channel" | "campaign";
  labelKey: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const visibleRows = sliceWithLimit(rows, SHOPIFY_TABLE_ROW_LIMIT, expanded);

  if (rows.length === 0) {
    return (
      <p className="shopify-empty-copy">
        Dati attribution disponibili solo dove Shopify ha registrato source, UTM o customer journey.
      </p>
    );
  }

  return (
    <>
      <table className="shopify-table">
        <thead>
          <tr>
            <th>{labelKey}</th>
            <th>Revenue</th>
            <th>Ordini</th>
          </tr>
        </thead>
        <tbody>
          {visibleRows.map((row) => {
            const keyValue = row[valueKey] ?? "unknown";
            return (
              <tr key={`${valueKey}-${keyValue}`}>
                <td>
                  {valueKey === "source" ? (
                    <span className={`shopify-source-chip ${sourceChipClass(String(keyValue))}`}>
                      {String(keyValue)}
                    </span>
                  ) : (
                    String(keyValue)
                  )}
                </td>
                <td>{formatMoney(row.revenue)}</td>
                <td>{row.ordersCount}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <ShowMoreToggle
        total={rows.length}
        limit={SHOPIFY_TABLE_ROW_LIMIT}
        expanded={expanded}
        onToggle={() => setExpanded((value) => !value)}
      />
    </>
  );
}

export function ShopifyAttributionIntelligencePanel({
  intelligence,
  availability,
  formatMoney,
}: ShopifyAttributionIntelligencePanelProps) {
  const hasData =
    availability.shopifyOrderAttributionAvailable ||
    intelligence.revenueBySource.length > 0 ||
    intelligence.revenueByChannel.length > 0;
  const score = intelligence.trackingQualityScore;
  const scoreClass =
    score >= 70
      ? "shopify-quality-score--good"
      : score >= 40
        ? "shopify-quality-score--mid"
        : "shopify-quality-score--low";

  return (
    <section className="shopify-attribution-intel gcr-card">
      <h3 className="shopify-panel__title">Shopify Attribution Intelligence</h3>
      <p className="shopify-attribution__sparse-note">
        Dati attribution disponibili solo dove Shopify ha registrato source, UTM o customer journey.
      </p>

      {!hasData ? (
        <p className="shopify-empty-copy">
          Attribution non disponibile dai dati ordine Shopify. Esegui un re-sync dopo il deploy per
          popolare source, channel e UTM dagli ordini.
        </p>
      ) : (
        <>
          <div className={`shopify-quality-score ${scoreClass}`}>
            <span className="shopify-quality-score__value">{score}%</span>
            <span className="shopify-quality-score__label">Tracking quality score</span>
          </div>

          <div className="shopify-attribution-metrics">
            <div className="shopify-attribution-metrics__item">
              <span className="shopify-attribution-metrics__value">
                {formatMoney(intelligence.unattributedRevenue)}
              </span>
              <span className="shopify-attribution-metrics__label">
                Unknown revenue ({intelligence.unattributedOrdersCount} ordini)
              </span>
            </div>
            <div className="shopify-attribution-metrics__item">
              <span className="shopify-attribution-metrics__value">
                {intelligence.directOrdersCount}
              </span>
              <span className="shopify-attribution-metrics__label">Ordini Direct</span>
            </div>
          </div>

          <h4 className="shopify-panel__subtitle">Revenue by channel</h4>
          <AttributionTable
            rows={intelligence.revenueByChannel}
            formatMoney={formatMoney}
            valueKey="channel"
            labelKey="Channel"
          />

          <h4 className="shopify-panel__subtitle">Revenue by source</h4>
          <AttributionTable
            rows={intelligence.revenueBySource}
            formatMoney={formatMoney}
            valueKey="source"
            labelKey="Source"
          />

          <h4 className="shopify-panel__subtitle">Top UTM campaigns</h4>
          <AttributionTable
            rows={intelligence.revenueByUtmCampaign}
            formatMoney={formatMoney}
            valueKey="campaign"
            labelKey="Campaign"
          />
        </>
      )}
    </section>
  );
}
