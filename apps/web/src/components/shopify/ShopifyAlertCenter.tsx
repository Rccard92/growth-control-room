import type { ShopifyDashboardAlert } from "@gcr/shared";

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
  if (alerts.length === 0) {
    return (
      <section className="shopify-alert-center gcr-card">
        <h3 className="shopify-panel__title">Alert Center</h3>
        <p className="shopify-empty-copy">Nessun alert al momento. Tutto sotto controllo.</p>
      </section>
    );
  }

  return (
    <section className="shopify-alert-center gcr-card">
      <h3 className="shopify-panel__title">Alert Center</h3>
      <p className="shopify-panel__subtitle">{alerts.length} alert prioritari</p>
      <ul className="shopify-alert-list">
        {alerts.slice(0, 12).map((alert) => (
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
    </section>
  );
}
