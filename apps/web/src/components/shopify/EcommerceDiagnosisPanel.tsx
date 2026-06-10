import type { ShopifyDailyDiagnosisItem, ShopifyInsightSeverity } from "@gcr/shared";
import { SHOPIFY_DIAGNOSIS_LIMIT } from "../../lib/shopify-dashboard-blocks";

interface EcommerceDiagnosisPanelProps {
  items: ShopifyDailyDiagnosisItem[];
}

const SEVERITY_LABELS: Record<string, string> = {
  critical: "Critico",
  warning: "Attenzione",
  opportunity: "Opportunità",
  info: "Info",
};

const SEVERITY_TITLES: Record<string, string> = {
  critical: "Intervento urgente",
  warning: "Attenzione operativa",
  opportunity: "Opportunità di crescita",
  info: "Nota operativa",
};

const SEVERITY_ACTIONS: Record<string, string> = {
  critical: "Intervieni subito",
  warning: "Verifica in Shopify",
  opportunity: "Valuta ottimizzazione",
  info: "Monitora l'andamento",
};

function deriveTitle(item: ShopifyDailyDiagnosisItem): string {
  const firstSentence = item.message.split(/[.!?]/)[0]?.trim();
  if (firstSentence && firstSentence.length <= 80) return firstSentence;
  return SEVERITY_TITLES[item.severity] ?? "Insight operativo";
}

function recommendedAction(severity: ShopifyInsightSeverity): string {
  return SEVERITY_ACTIONS[severity] ?? "Verifica in Shopify";
}

export function EcommerceDiagnosisPanel({ items }: EcommerceDiagnosisPanelProps) {
  const visibleItems = items.slice(0, SHOPIFY_DIAGNOSIS_LIMIT);

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
        {visibleItems.map((item, index) => (
          <li key={`${item.severity}-${index}`} className="shopify-diagnosis__card">
            <div className="shopify-diagnosis__card-head">
              <span className={`shopify-severity shopify-severity--${item.severity}`}>
                {SEVERITY_LABELS[item.severity] ?? item.severity}
              </span>
              <span className="shopify-diagnosis__action">{recommendedAction(item.severity)}</span>
            </div>
            <h4 className="shopify-diagnosis__title">{deriveTitle(item)}</h4>
            <p className="shopify-diagnosis__message">{item.message}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

export { EcommerceDiagnosisPanel as DailyDiagnosisPanel };
