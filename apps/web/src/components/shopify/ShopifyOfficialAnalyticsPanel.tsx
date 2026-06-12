import { useState } from "react";
import type { ShopifyOfficialAnalytics } from "@gcr/shared";
import {
  SHOPIFY_TABLE_ROW_LIMIT,
  sliceWithLimit,
} from "../../lib/shopify-dashboard-blocks";
import { ShowMoreToggle } from "./ShowMoreToggle";

interface ShopifyOfficialAnalyticsPanelProps {
  officialAnalytics: ShopifyOfficialAnalytics;
  formatMoney: (value: string) => string;
}

function formatPercent(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${value.toFixed(1)}%`;
}

export function ShopifyOfficialAnalyticsPanel({
  officialAnalytics,
  formatMoney,
}: ShopifyOfficialAnalyticsPanelProps) {
  const [channelExpanded, setChannelExpanded] = useState(false);
  const [utmExpanded, setUtmExpanded] = useState(false);
  const { kpis, timeseries, salesByReferringChannel, salesByUtmCampaign, dataQuality } =
    officialAnalytics;

  const maxSales = Math.max(
    ...timeseries.map((point) => Number(point.totalSales ?? 0)),
    1,
  );

  const visibleChannels = sliceWithLimit(
    salesByReferringChannel,
    SHOPIFY_TABLE_ROW_LIMIT,
    channelExpanded,
  );
  const visibleUtm = sliceWithLimit(
    salesByUtmCampaign,
    SHOPIFY_TABLE_ROW_LIMIT,
    utmExpanded,
  );

  return (
    <section className="shopify-official-analytics gcr-card">
      <div className="shopify-official-analytics__header">
        <div>
          <h2 className="shopify-panel__title">Shopify Official Analytics</h2>
          <p className="shopify-panel__context">
            Metriche ufficiali dalla dashboard Analytics Shopify
          </p>
        </div>
        <span className="shopify-official-badge">Powered by ShopifyQL</span>
      </div>

      {dataQuality.status !== "ok" && dataQuality.warnings.length > 0 && (
        <div className="shopify-official-analytics__banner">
          {dataQuality.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}

      <div className="shopify-official-analytics__kpis">
        <div className="shopify-official-analytics__kpi">
          <span className="shopify-official-analytics__kpi-label">Total sales</span>
          <span className="shopify-official-analytics__kpi-value">
            {kpis.totalSales != null ? formatMoney(kpis.totalSales) : "—"}
          </span>
        </div>
        <div className="shopify-official-analytics__kpi">
          <span className="shopify-official-analytics__kpi-label">Orders</span>
          <span className="shopify-official-analytics__kpi-value">
            {kpis.orders ?? "—"}
          </span>
        </div>
        <div className="shopify-official-analytics__kpi">
          <span className="shopify-official-analytics__kpi-label">Sessions</span>
          <span className="shopify-official-analytics__kpi-value">
            {kpis.sessions ?? "—"}
          </span>
        </div>
        <div className="shopify-official-analytics__kpi">
          <span className="shopify-official-analytics__kpi-label">Conversion rate</span>
          <span className="shopify-official-analytics__kpi-value">
            {formatPercent(kpis.conversionRate)}
          </span>
        </div>
        <div className="shopify-official-analytics__kpi">
          <span className="shopify-official-analytics__kpi-label">AOV</span>
          <span className="shopify-official-analytics__kpi-value">
            {kpis.averageOrderValue != null ? formatMoney(kpis.averageOrderValue) : "—"}
          </span>
        </div>
      </div>

      {timeseries.length > 0 && (
        <div className="shopify-official-analytics__section">
          <h3 className="shopify-panel__subtitle">Sales over time</h3>
          <div className="shopify-timeseries-bars">
            {timeseries.map((point) => {
              const salesValue = Number(point.totalSales ?? 0);
              const width = Math.max(4, (salesValue / maxSales) * 100);
              return (
                <div key={point.date} className="shopify-timeseries-bars__row">
                  <span className="shopify-timeseries-bars__date">{point.date}</span>
                  <div className="shopify-timeseries-bars__track">
                    <div
                      className="shopify-timeseries-bars__bar"
                      style={{ width: `${width}%` }}
                    />
                  </div>
                  <span className="shopify-timeseries-bars__value">
                    {point.totalSales != null ? formatMoney(point.totalSales) : "—"}
                  </span>
                  <span className="shopify-timeseries-bars__meta">{point.orders ?? 0} ord.</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {salesByReferringChannel.length > 0 && (
        <div className="shopify-official-analytics__section">
          <div className="shopify-official-analytics__section-header">
            <h3 className="shopify-panel__subtitle">Sales by referring channel</h3>
            <ShowMoreToggle
              total={salesByReferringChannel.length}
              limit={SHOPIFY_TABLE_ROW_LIMIT}
              expanded={channelExpanded}
              onToggle={() => setChannelExpanded((value) => !value)}
            />
          </div>
          <table className="shopify-table">
            <thead>
              <tr>
                <th>Channel</th>
                <th>Total sales</th>
                <th>Orders</th>
              </tr>
            </thead>
            <tbody>
              {visibleChannels.map((row) => (
                <tr key={row.channel}>
                  <td>{row.channel}</td>
                  <td>{formatMoney(row.totalSales)}</td>
                  <td>{row.orders}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {salesByUtmCampaign.length > 0 && (
        <div className="shopify-official-analytics__section">
          <div className="shopify-official-analytics__section-header">
            <h3 className="shopify-panel__subtitle">Sales by UTM campaign</h3>
            <ShowMoreToggle
              total={salesByUtmCampaign.length}
              limit={SHOPIFY_TABLE_ROW_LIMIT}
              expanded={utmExpanded}
              onToggle={() => setUtmExpanded((value) => !value)}
            />
          </div>
          <table className="shopify-table">
            <thead>
              <tr>
                <th>Campaign</th>
                <th>Source</th>
                <th>Medium</th>
                <th>Total sales</th>
                <th>Orders</th>
              </tr>
            </thead>
            <tbody>
              {visibleUtm.map((row) => (
                <tr key={`${row.name}-${row.source}-${row.medium}`}>
                  <td>{row.name}</td>
                  <td>{row.source}</td>
                  <td>{row.medium}</td>
                  <td>{formatMoney(row.totalSales)}</td>
                  <td>{row.orders}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
