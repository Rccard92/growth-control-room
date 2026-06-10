import { useState } from "react";
import type { ShopifyProductPerformanceSection } from "@gcr/shared";

interface ProductIntelligencePanelProps {
  performance: ShopifyProductPerformanceSection;
  formatMoney: (value: string) => string;
}

type Tab = "best" | "stale" | "highstock" | "seo";

const TABS: { id: Tab; label: string }[] = [
  { id: "best", label: "Best seller" },
  { id: "stale", label: "Prodotti fermi" },
  { id: "highstock", label: "Stock alto" },
  { id: "seo", label: "SEO incompleto" },
];

export function ProductIntelligencePanel({
  performance,
  formatMoney,
}: ProductIntelligencePanelProps) {
  const [tab, setTab] = useState<Tab>("best");

  const seoIncomplete = performance.noSalesProducts.filter((p) => p.seoIssue);

  return (
    <section className="shopify-product-intel gcr-card">
      <h3 className="shopify-panel__title">Product Intelligence</h3>
      <div className="shopify-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`shopify-tabs__btn ${tab === t.id ? "shopify-tabs__btn--active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "best" && (
        <table className="shopify-table">
          <thead>
            <tr>
              <th>Prodotto</th>
              <th>SKU</th>
              <th>Qty</th>
              <th>Revenue</th>
              <th>Stock</th>
            </tr>
          </thead>
          <tbody>
            {performance.bestSellers.length === 0 ? (
              <tr>
                <td colSpan={5} className="shopify-empty-copy">
                  Nessun best seller. Re-sync per popolare line items con prezzi.
                </td>
              </tr>
            ) : (
              performance.bestSellers.map((item) => (
                <tr key={item.productTitle}>
                  <td>{item.productTitle}</td>
                  <td>{item.sku ?? "—"}</td>
                  <td>{item.quantitySold}</td>
                  <td>{formatMoney(item.revenue)}</td>
                  <td>{item.currentInventory ?? "—"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}

      {tab === "stale" && (
        <table className="shopify-table">
          <thead>
            <tr>
              <th>Prodotto</th>
              <th>Stock</th>
              <th>Tipo</th>
              <th>SEO</th>
            </tr>
          </thead>
          <tbody>
            {performance.noSalesProducts.length === 0 ? (
              <tr>
                <td colSpan={4} className="shopify-empty-copy">
                  Tutti i prodotti attivi compaiono negli ordini sincronizzati.
                </td>
              </tr>
            ) : (
              performance.noSalesProducts.map((item) => (
                <tr key={item.productTitle}>
                  <td>{item.productTitle}</td>
                  <td>{item.currentInventory ?? "—"}</td>
                  <td>{item.productType ?? "—"}</td>
                  <td>{item.seoIssue ? "Incompleto" : "OK"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}

      {tab === "highstock" && (
        <table className="shopify-table">
          <thead>
            <tr>
              <th>Prodotto</th>
              <th>Stock</th>
              <th>Vendite</th>
              <th>Issue</th>
            </tr>
          </thead>
          <tbody>
            {performance.highStockLowSales.length === 0 ? (
              <tr>
                <td colSpan={4} className="shopify-empty-copy">
                  Nessun prodotto con stock alto e vendite basse.
                </td>
              </tr>
            ) : (
              performance.highStockLowSales.map((item) => (
                <tr key={item.productTitle}>
                  <td>{item.productTitle}</td>
                  <td>{item.currentInventory ?? "—"}</td>
                  <td>{item.quantitySold}</td>
                  <td>{item.issue}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}

      {tab === "seo" && (
        <table className="shopify-table">
          <thead>
            <tr>
              <th>Prodotto</th>
              <th>Stock</th>
              <th>Stato SEO</th>
            </tr>
          </thead>
          <tbody>
            {seoIncomplete.length === 0 ? (
              <tr>
                <td colSpan={3} className="shopify-empty-copy">
                  Nessun prodotto fermo con SEO incompleto.
                </td>
              </tr>
            ) : (
              seoIncomplete.map((item) => (
                <tr key={item.productTitle}>
                  <td>{item.productTitle}</td>
                  <td>{item.currentInventory ?? "—"}</td>
                  <td>Incompleto</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}
    </section>
  );
}
