import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  filterGrowthAuditEconomicPriorityItems,
  getGrowthAuditEconomicPriorityLevelBadgeClass,
  type GrowthAuditEconomicPriorityFilter,
  type GrowthAuditEconomicPriorityItem,
} from "../../lib/growth-audit-utils";
import { APP_ROUTES } from "../../routes/config";

interface GrowthAuditEconomicPriorityPanelProps {
  projectId: string;
  runId: string;
  items: GrowthAuditEconomicPriorityItem[];
  maxItems?: number;
}

const FILTER_OPTIONS: { id: GrowthAuditEconomicPriorityFilter; label: string }[] = [
  { id: "all", label: "Tutti" },
  { id: "high_priority", label: "Priorità massima/alta" },
  { id: "with_sales", label: "Con vendite" },
  { id: "high_impressions", label: "Con molte impression" },
  { id: "with_funnel", label: "Con funnel ecommerce" },
  { id: "stock_issues", label: "Con problemi stock" },
  { id: "incomplete_data", label: "Dati incompleti" },
];

function formatMoney(value?: number | null, currency = "EUR"): string {
  if (value == null) return "—";
  return `${value.toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
}

function formatPercent(value?: number | null): string {
  if (value == null) return "—";
  return `${(value * 100).toLocaleString("it-IT", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
}

function formatNumber(value?: number | null): string {
  if (value == null) return "—";
  return value.toLocaleString("it-IT");
}

function formatSalesRevenue(item: GrowthAuditEconomicPriorityItem): string {
  if (item.metrics.sales != null && item.metrics.sales > 0) {
    return `Revenue Shopify: ${formatMoney(item.metrics.sales)}`;
  }
  if (item.metrics.itemRevenue != null && item.metrics.itemRevenue > 0) {
    return `Revenue GA4: ${formatMoney(item.metrics.itemRevenue)}`;
  }
  return "—";
}

function formatGscSummary(item: GrowthAuditEconomicPriorityItem): string {
  const impressions = item.metrics.gscImpressions;
  const ctr = item.metrics.gscCtr;
  if (impressions == null) return "—";
  const ctrPart = ctr != null ? ` · CTR ${formatPercent(ctr)}` : "";
  return `${formatNumber(impressions)} imp${ctrPart}`;
}

function formatFunnelSummary(item: GrowthAuditEconomicPriorityItem): string {
  const views = item.metrics.itemViews;
  const purchases = item.metrics.purchases;
  if (views == null) return "—";
  const purchasePart =
    purchases != null ? ` · ${formatNumber(purchases)} purchase` : "";
  return `${formatNumber(views)} view${purchasePart}`;
}

export function GrowthAuditEconomicPriorityPanel({
  projectId,
  runId,
  items,
  maxItems = 10,
}: GrowthAuditEconomicPriorityPanelProps) {
  const [activeFilter, setActiveFilter] =
    useState<GrowthAuditEconomicPriorityFilter>("all");

  const filteredItems = useMemo(
    () => filterGrowthAuditEconomicPriorityItems(items, activeFilter).slice(0, maxItems),
    [items, activeFilter, maxItems],
  );

  return (
    <section className="growth-audit-economic-priority gcr-card">
      <header className="growth-audit-economic-priority__header">
        <div>
          <h2 className="growth-audit-economic-priority__title">Prodotti da migliorare prima</h2>
          <p className="growth-audit-economic-priority__subtitle">
            Classifica basata su vendite, traffico, funnel ecommerce, SEO organica, performance e
            criticità CRO.
          </p>
        </div>
      </header>

      <div className="growth-audit-economic-priority__filters" role="tablist">
        {FILTER_OPTIONS.map((option) => (
          <button
            key={option.id}
            type="button"
            role="tab"
            aria-selected={activeFilter === option.id}
            className={
              activeFilter === option.id
                ? "growth-audit-economic-priority__filter growth-audit-economic-priority__filter--active"
                : "growth-audit-economic-priority__filter"
            }
            onClick={() => setActiveFilter(option.id)}
          >
            {option.label}
          </button>
        ))}
      </div>

      {filteredItems.length === 0 ? (
        <p className="growth-audit-economic-priority__empty">
          Nessun prodotto corrisponde al filtro selezionato.
        </p>
      ) : (
        <>
          <div className="growth-audit-economic-priority__table-wrap">
            <table className="growth-audit-economic-priority__table">
              <thead>
                <tr>
                  <th>Priorità</th>
                  <th>Prodotto</th>
                  <th>Motivo principale</th>
                  <th>Vendite / Revenue</th>
                  <th>GSC</th>
                  <th>GA4 Funnel</th>
                  <th>Stock</th>
                  <th>Azione</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => (
                  <tr key={item.pageId} className="growth-audit-economic-priority__row">
                    <td>
                      <div className="growth-audit-economic-priority__score-cell">
                        <span className={getGrowthAuditEconomicPriorityLevelBadgeClass(item.level)}>
                          {item.label}
                        </span>
                        <strong className="growth-audit-economic-priority__score">
                          {item.score}
                        </strong>
                      </div>
                    </td>
                    <td>
                      <strong>{item.title}</strong>
                      {item.handle && (
                        <span className="growth-audit-economic-priority__handle">/{item.handle}</span>
                      )}
                    </td>
                    <td>
                      <p className="growth-audit-economic-priority__reason">{item.shortReason}</p>
                    </td>
                    <td className="growth-audit-economic-priority__metrics">
                      {formatSalesRevenue(item)}
                    </td>
                    <td className="growth-audit-economic-priority__metrics">
                      {formatGscSummary(item)}
                    </td>
                    <td className="growth-audit-economic-priority__metrics">
                      {formatFunnelSummary(item)}
                    </td>
                    <td className="growth-audit-economic-priority__metrics">
                      {item.metrics.stock != null ? formatNumber(item.metrics.stock) : "—"}
                    </td>
                    <td>
                      <Link
                        to={APP_ROUTES.projectGrowthAuditPageDetail(projectId, runId, item.pageId)}
                        className="gcr-btn gcr-btn--primary gcr-btn--sm"
                      >
                        Apri pagina
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <ul className="growth-audit-economic-priority__cards">
            {filteredItems.map((item) => (
              <li key={item.pageId} className="growth-audit-economic-priority__card">
                <div className="growth-audit-economic-priority__card-header">
                  <span className={getGrowthAuditEconomicPriorityLevelBadgeClass(item.level)}>
                    {item.label}
                  </span>
                  <strong className="growth-audit-economic-priority__score">{item.score}</strong>
                </div>
                <h3 className="growth-audit-economic-priority__card-title">{item.title}</h3>
                <p className="growth-audit-economic-priority__reason">{item.shortReason}</p>
                <div className="growth-audit-economic-priority__card-metrics">
                  <span>{formatSalesRevenue(item)}</span>
                  <span>GSC: {formatGscSummary(item)}</span>
                  <span>Funnel: {formatFunnelSummary(item)}</span>
                  <span>
                    Stock:{" "}
                    {item.metrics.stock != null ? formatNumber(item.metrics.stock) : "—"}
                  </span>
                </div>
                <Link
                  to={APP_ROUTES.projectGrowthAuditPageDetail(projectId, runId, item.pageId)}
                  className="gcr-btn gcr-btn--primary gcr-btn--sm"
                >
                  Apri pagina
                </Link>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
