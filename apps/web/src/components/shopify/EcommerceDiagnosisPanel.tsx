import type { ShopifyDailyDiagnosisItem } from "@gcr/shared";

interface EcommerceDiagnosisPanelProps {
  items: ShopifyDailyDiagnosisItem[];
}

const SEVERITY_LABELS: Record<string, string> = {
  critical: "Critico",
  warning: "Attenzione",
  opportunity: "Opportunità",
  info: "Info",
};

export function EcommerceDiagnosisPanel({ items }: EcommerceDiagnosisPanelProps) {
  if (items.length === 0) {
    return (
      <section className="shopify-diagnosis gcr-card">
        <h3 className="shopify-panel__title">Daily Ecommerce Diagnosis</h3>
        <p className="shopify-empty-copy">
          Nessun insight disponibile. Esegui una sincronizzazione per generare il briefing.
        </p>
      </section>
    );
  }

  return (
    <section className="shopify-diagnosis gcr-card">
      <h3 className="shopify-panel__title">Daily Ecommerce Diagnosis</h3>
      <p className="shopify-diagnosis__subtitle">Briefing operativo della giornata</p>
      <ul className="shopify-diagnosis__list">
        {items.map((item, index) => (
          <li key={`${item.severity}-${index}`} className="shopify-diagnosis__item">
            <span className={`shopify-severity shopify-severity--${item.severity}`}>
              {SEVERITY_LABELS[item.severity] ?? item.severity}
            </span>
            <span className="shopify-diagnosis__message">{item.message}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
