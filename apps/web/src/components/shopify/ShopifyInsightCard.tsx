import type { ShopifyInsight } from "@gcr/shared";

interface ShopifyInsightCardProps {
  insights: ShopifyInsight[];
}

const SEVERITY_LABELS: Record<string, string> = {
  info: "Info",
  warning: "Attenzione",
  critical: "Critico",
  opportunity: "Opportunità",
};

export function ShopifyInsightCard({ insights }: ShopifyInsightCardProps) {
  return (
    <div className="shopify-panel shopify-panel--insights">
      <div className="shopify-panel__header">
        <h3 className="shopify-panel__title">Growth Insights</h3>
        <p className="shopify-panel__subtitle">Segnali operativi dal tuo store</p>
      </div>
      {!insights.length ? (
        <p className="shopify-empty-copy">Nessun insight al momento. I dati sono in equilibrio.</p>
      ) : (
        <ul className="shopify-insights">
          {insights.map((insight) => (
            <li key={`${insight.severity}-${insight.message}`} className="shopify-insights__item">
              <span className={`shopify-badge shopify-badge--${insight.severity}`}>
                {SEVERITY_LABELS[insight.severity] ?? insight.severity}
              </span>
              <p>{insight.message}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
