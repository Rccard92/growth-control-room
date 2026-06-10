import { useState } from "react";
import type { ShopifyDashboardAlert } from "@gcr/shared";
import { SHOPIFY_TABLE_ROW_LIMIT, sliceWithLimit } from "../../lib/shopify-dashboard-blocks";
import { ShowMoreToggle } from "./ShowMoreToggle";

interface ShopifyAlertCenterProps {
  alerts: ShopifyDashboardAlert[];
}

const SEVERITY_LABELS: Record<string, string> = {
  critical: "Critico",
  warning: "Warning",
  opportunity: "Opportunità",
  info: "Info",
};

export function ShopifyAlertCenter({ alerts }: ShopifyAlertCenterProps) {
  const [expanded, setExpanded] = useState(false);

  const criticalCount = alerts.filter((a) => a.severity === "critical").length;
  const warningCount = alerts.filter((a) => a.severity === "warning").length;
  const prominentClass = criticalCount > 0 ? "shopify-alert-center--prominent" : "";
  const visibleAlerts = sliceWithLimit(alerts, SHOPIFY_TABLE_ROW_LIMIT, expanded);

  if (alerts.length === 0) {
    return (
      <section className="shopify-alert-center gcr-card">
        <h3 className="shopify-panel__title">Alert Center</h3>
        <p className="shopify-empty-copy">Nessun alert al momento. Tutto sotto controllo.</p>
      </section>
    );
  }

  return (
    <section className={`shopify-alert-center gcr-card ${prominentClass}`}>
      <div className="shopify-alert-center__head">
        <div>
          <h3 className="shopify-panel__title">Alert Center</h3>
          <p className="shopify-panel__subtitle">{alerts.length} alert prioritari</p>
        </div>
        <div className="shopify-alert-center__counts">
          {criticalCount > 0 && (
            <span className="shopify-severity shopify-severity--critical">
              {criticalCount} critici
            </span>
          )}
          {warningCount > 0 && (
            <span className="shopify-severity shopify-severity--warning">
              {warningCount} warning
            </span>
          )}
        </div>
      </div>
      <ul className="shopify-alert-list">
        {visibleAlerts.map((alert) => (
          <li key={alert.id} className="shopify-alert-item">
            <div className="shopify-alert-item__head">
              <span className={`shopify-severity shopify-severity--${alert.severity}`}>
                {SEVERITY_LABELS[alert.severity] ?? alert.severity}
              </span>
              <span className="shopify-alert-item__type">{alert.entityType}</span>
            </div>
            <p className="shopify-alert-item__title">{alert.title}</p>
            <p className="shopify-alert-item__desc">{alert.description}</p>
            {alert.actionLabel && (
              <span className="shopify-alert-item__action">{alert.actionLabel}</span>
            )}
          </li>
        ))}
      </ul>
      <ShowMoreToggle
        total={alerts.length}
        limit={SHOPIFY_TABLE_ROW_LIMIT}
        expanded={expanded}
        onToggle={() => setExpanded((value) => !value)}
      />
    </section>
  );
}
