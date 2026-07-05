import type { GrowthAuditPage } from "@gcr/shared";
import {
  getGrowthAuditPageGa4EcommerceMetadata,
  isGrowthAuditProductPage,
} from "../../../lib/growth-audit-utils";

interface GrowthAuditPageWorkspaceGa4EcommerceSectionProps {
  page: GrowthAuditPage;
}

function formatNumber(value?: number | null): string {
  if (value == null) return "—";
  return value.toLocaleString("it-IT");
}

function formatMoney(value?: number | null, currency?: string | null): string {
  if (value == null) return "—";
  const formatted = value.toLocaleString("it-IT", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return currency ? `${formatted} ${currency}` : formatted;
}

function formatRate(value?: number | null): string {
  if (value == null) return "—";
  return `${(value * 100).toLocaleString("it-IT", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

function buildFunnelDiagnosis(
  meta: NonNullable<ReturnType<typeof getGrowthAuditPageGa4EcommerceMetadata>>,
): string | null {
  const itemViews = meta.itemViews ?? meta.itemViewEvents ?? 0;
  const itemsAddedToCart = meta.itemsAddedToCart ?? 0;
  const itemsCheckedOut = meta.itemsCheckedOut ?? 0;
  const itemsPurchased = meta.itemsPurchased ?? 0;

  if (meta.matchedBy === "none") {
    return "GA4 non ha restituito un match affidabile per questo prodotto. Controlla item_id / SKU / tracking ecommerce.";
  }
  if (itemViews > 50 && itemsAddedToCart === 0) {
    return "Il prodotto viene visto ma non entra nel carrello. Problema probabile: offerta, prezzo, trust, immagini o CTA.";
  }
  if (itemsAddedToCart > 0 && itemsCheckedOut === 0) {
    return "Gli utenti aggiungono al carrello ma non iniziano il checkout. Verifica costi, spedizione, carrello e fiducia.";
  }
  if (itemsCheckedOut > 0 && itemsPurchased === 0) {
    return "Gli utenti arrivano al checkout ma non acquistano. Verifica checkout, pagamento, spedizione e costi finali.";
  }
  if (itemsPurchased > 0) {
    return "Il prodotto genera acquisti. Migliorare la pagina può amplificare una domanda già validata.";
  }
  return null;
}

export function GrowthAuditPageWorkspaceGa4EcommerceSection({
  page,
}: GrowthAuditPageWorkspaceGa4EcommerceSectionProps) {
  if (!isGrowthAuditProductPage(page)) {
    return null;
  }

  const funnelMeta = getGrowthAuditPageGa4EcommerceMetadata(page);
  const diagnosis = funnelMeta ? buildFunnelDiagnosis(funnelMeta) : null;

  const funnelSteps = funnelMeta
    ? [
        {
          label: "View item",
          value: formatNumber(funnelMeta.itemViews ?? funnelMeta.itemViewEvents),
        },
        {
          label: "Add to cart",
          value: formatNumber(funnelMeta.itemsAddedToCart),
        },
        {
          label: "Begin checkout",
          value: formatNumber(funnelMeta.itemsCheckedOut),
        },
        {
          label: "Purchase",
          value: formatNumber(funnelMeta.itemsPurchased),
        },
      ]
    : [];

  return (
    <section
      id="ga4-ecommerce-funnel"
      className="growth-audit-ga4-funnel growth-audit-workspace-section gcr-card"
    >
      <header className="growth-audit-workspace-section__header">
        <h2 className="growth-audit-workspace-section__title">GA4 Ecommerce Funnel</h2>
        <p className="growth-audit-workspace-section__subtitle">
          Mostra il percorso ecommerce item-level del prodotto: visualizzazione, carrello,
          checkout e acquisto.
        </p>
      </header>

      {funnelMeta ? (
        <>
          <div className="growth-audit-ga4-funnel__steps">
            {funnelSteps.map((step, index) => (
              <div key={step.label} className="growth-audit-ga4-funnel__step-wrap">
                {index > 0 && <span className="growth-audit-ga4-funnel__arrow">→</span>}
                <div className="growth-audit-ga4-funnel__step">
                  <span className="growth-audit-ga4-funnel__step-label">{step.label}</span>
                  <strong className="growth-audit-ga4-funnel__step-value">{step.value}</strong>
                </div>
              </div>
            ))}
          </div>

          <div className="growth-audit-ga4-funnel__rates">
            <div>
              <span>Item revenue</span>
              <strong>{formatMoney(funnelMeta.itemRevenue, funnelMeta.currency)}</strong>
            </div>
            <div>
              <span>View → cart</span>
              <strong>{formatRate(funnelMeta.viewToCartRate)}</strong>
            </div>
            <div>
              <span>Cart → checkout</span>
              <strong>{formatRate(funnelMeta.cartToCheckoutRate)}</strong>
            </div>
            <div>
              <span>Checkout → purchase</span>
              <strong>{formatRate(funnelMeta.checkoutToPurchaseRate)}</strong>
            </div>
            <div>
              <span>View → purchase</span>
              <strong>{formatRate(funnelMeta.viewToPurchaseRate)}</strong>
            </div>
            <div>
              <span>Cart → purchase</span>
              <strong>{formatRate(funnelMeta.cartToPurchaseRate)}</strong>
            </div>
          </div>

          <p className="growth-audit-ga4-funnel__match">
            Match GA4: <strong>{funnelMeta.matchedBy ?? "none"}</strong>
            {funnelMeta.matchedItemIds && funnelMeta.matchedItemIds.length > 0
              ? ` · ID: ${funnelMeta.matchedItemIds.join(", ")}`
              : ""}
          </p>

          {diagnosis && (
            <p className="growth-audit-ga4-funnel__diagnosis">{diagnosis}</p>
          )}
        </>
      ) : (
        <p className="growth-audit-ga4-funnel__empty">
          Questa pagina non ha ancora dati funnel ecommerce GA4 nella run attuale.
        </p>
      )}
    </section>
  );
}
