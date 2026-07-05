import type { GrowthAuditPage } from "@gcr/shared";
import {
  getGrowthAuditPageShopifyCommerceMetadata,
  isGrowthAuditProductPage,
} from "../../../lib/growth-audit-utils";

interface GrowthAuditPageWorkspaceShopifyCommerceSectionProps {
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

function formatAvailability(value?: boolean | null): string {
  if (value == null) return "—";
  return value ? "Disponibile" : "Non disponibile";
}

function formatPriceRange(
  priceMin?: number | null,
  priceMax?: number | null,
  currency?: string | null,
): string {
  if (priceMin == null && priceMax == null) return "—";
  if (priceMin != null && priceMax != null && priceMin !== priceMax) {
    return `Da ${formatMoney(priceMin, currency)} a ${formatMoney(priceMax, currency)}`;
  }
  return formatMoney(priceMin ?? priceMax, currency);
}

export function GrowthAuditPageWorkspaceShopifyCommerceSection({
  page,
}: GrowthAuditPageWorkspaceShopifyCommerceSectionProps) {
  if (!isGrowthAuditProductPage(page)) {
    return null;
  }

  const commerceMeta = getGrowthAuditPageShopifyCommerceMetadata(page);

  return (
    <section
      id="shopify-commerce"
      className="growth-audit-shopify-commerce growth-audit-workspace-section gcr-card"
    >
      <header className="growth-audit-workspace-section__header">
        <h2 className="growth-audit-workspace-section__title">Shopify Commerce</h2>
        <p className="growth-audit-workspace-section__subtitle">
          Questi dati aiutano a capire il peso economico reale della pagina prodotto.
        </p>
      </header>

      {commerceMeta ? (
        <div className="growth-audit-shopify-commerce__grid">
          <div className="growth-audit-shopify-commerce__metric growth-audit-shopify-commerce__metric--highlight">
            <span className="growth-audit-shopify-commerce__metric-label">Revenue / Sales</span>
            <strong className="growth-audit-shopify-commerce__metric-value">
              {formatMoney(commerceMeta.sales, commerceMeta.currency)}
            </strong>
          </div>
          <div className="growth-audit-shopify-commerce__metric">
            <span className="growth-audit-shopify-commerce__metric-label">Quantità venduta</span>
            <strong className="growth-audit-shopify-commerce__metric-value">
              {formatNumber(commerceMeta.quantitySold)}
            </strong>
          </div>
          <div className="growth-audit-shopify-commerce__metric">
            <span className="growth-audit-shopify-commerce__metric-label">Ordini</span>
            <strong className="growth-audit-shopify-commerce__metric-value">
              {formatNumber(commerceMeta.ordersCount)}
            </strong>
          </div>
          <div className="growth-audit-shopify-commerce__metric">
            <span className="growth-audit-shopify-commerce__metric-label">Stock</span>
            <strong
              className={`growth-audit-shopify-commerce__metric-value${
                commerceMeta.stock != null && commerceMeta.stock <= 0
                  ? " growth-audit-shopify-commerce__status--danger"
                  : commerceMeta.stock != null && commerceMeta.stock <= 10
                    ? " growth-audit-shopify-commerce__status--warning"
                    : ""
              }`}
            >
              {formatNumber(commerceMeta.stock)}
            </strong>
          </div>
          <div className="growth-audit-shopify-commerce__metric">
            <span className="growth-audit-shopify-commerce__metric-label">Disponibilità</span>
            <strong
              className={`growth-audit-shopify-commerce__metric-value${
                commerceMeta.availableForSale === false
                  ? " growth-audit-shopify-commerce__status--danger"
                  : commerceMeta.availableForSale === true
                    ? " growth-audit-shopify-commerce__status--good"
                    : ""
              }`}
            >
              {formatAvailability(commerceMeta.availableForSale)}
            </strong>
          </div>
          <div className="growth-audit-shopify-commerce__metric">
            <span className="growth-audit-shopify-commerce__metric-label">Prezzo</span>
            <strong className="growth-audit-shopify-commerce__metric-value">
              {formatPriceRange(
                commerceMeta.priceMin,
                commerceMeta.priceMax,
                commerceMeta.currency,
              )}
            </strong>
          </div>
          <div className="growth-audit-shopify-commerce__metric">
            <span className="growth-audit-shopify-commerce__metric-label">Periodo</span>
            <strong className="growth-audit-shopify-commerce__metric-value">
              {commerceMeta.periodDays != null ? `${commerceMeta.periodDays} giorni` : "—"}
            </strong>
          </div>
        </div>
      ) : (
        <p className="growth-audit-shopify-commerce__empty">
          Questa pagina non ha ancora dati ecommerce Shopify nella run attuale.
        </p>
      )}
    </section>
  );
}
