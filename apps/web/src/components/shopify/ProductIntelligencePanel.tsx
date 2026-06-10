import { useState } from "react";
import type { ShopifyProductPerformanceSection } from "@gcr/shared";
import { SHOPIFY_TABLE_ROW_LIMIT } from "../../lib/shopify-dashboard-blocks";
import { ShowMoreToggle } from "./ShowMoreToggle";

interface ProductIntelligencePanelProps {
  productIntelligence: ShopifyProductPerformanceSection;
  formatMoney: (value: string) => string;
  periodLabel?: string;
}

type Tab = "best" | "stale" | "highstock" | "seo";

const TABS: { id: Tab; label: string }[] = [
  { id: "best", label: "Best seller" },
  { id: "stale", label: "Senza vendite" },
  { id: "highstock", label: "Stock alto/vendite basse" },
  { id: "seo", label: "Issue SEO" },
];

export function ProductIntelligencePanel({
  productIntelligence,
  formatMoney,
  periodLabel,
}: ProductIntelligencePanelProps) {
  const [tab, setTab] = useState<Tab>("best");
  const [expanded, setExpanded] = useState(false);

  const seoIncomplete = productIntelligence.noSalesProducts.filter((p) => p.seoIssue);

  return (
    <section className="shopify-product-intel gcr-card">
      <h3 className="shopify-panel__title">Product Intelligence</h3>
      {periodLabel && (
        <p className="shopify-panel__context">Vendite e performance nel periodo: {periodLabel}</p>
      )}
      <div className="shopify-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`shopify-tabs__btn ${tab === t.id ? "shopify-tabs__btn--active" : ""}`}
            onClick={() => {
              setTab(t.id);
              setExpanded(false);
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "best" && (
        <>
          <table className="shopify-table">
            <thead>
              <tr>
                <th>Prodotto</th>
                <th>Qty</th>
                <th>Revenue</th>
                <th>Stock</th>
                <th>Status</th>
                <th>Issue</th>
              </tr>
            </thead>
            <tbody>
              {productIntelligence.bestSellers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="shopify-empty-copy">
                    Nessun best seller. Re-sync per popolare line items con prezzi.
                  </td>
                </tr>
              ) : (
                productIntelligence.bestSellers
                  .slice(0, expanded ? undefined : SHOPIFY_TABLE_ROW_LIMIT)
                  .map((item) => (
                    <tr key={item.productTitle}>
                      <td>{item.productTitle}</td>
                      <td>{item.quantitySold}</td>
                      <td>{formatMoney(item.revenue)}</td>
                      <td>{item.currentInventory ?? "—"}</td>
                      <td>{item.status ?? "—"}</td>
                      <td>—</td>
                    </tr>
                  ))
              )}
            </tbody>
          </table>
          <ShowMoreToggle
            total={productIntelligence.bestSellers.length}
            limit={SHOPIFY_TABLE_ROW_LIMIT}
            expanded={expanded}
            onToggle={() => setExpanded((value) => !value)}
          />
        </>
      )}

      {tab === "stale" && (
        <>
          <table className="shopify-table">
            <thead>
              <tr>
                <th>Prodotto</th>
                <th>Qty</th>
                <th>Revenue</th>
                <th>Stock</th>
                <th>Status</th>
                <th>Issue</th>
              </tr>
            </thead>
            <tbody>
              {productIntelligence.noSalesProducts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="shopify-empty-copy">
                    Tutti i prodotti attivi compaiono negli ordini sincronizzati.
                  </td>
                </tr>
              ) : (
                productIntelligence.noSalesProducts
                  .slice(0, expanded ? undefined : SHOPIFY_TABLE_ROW_LIMIT)
                  .map((item) => (
                    <tr key={item.productTitle}>
                      <td>{item.productTitle}</td>
                      <td>0</td>
                      <td>{formatMoney("0")}</td>
                      <td>{item.currentInventory ?? "—"}</td>
                      <td>{item.status ?? "—"}</td>
                      <td>{item.seoIssue ? "SEO incompleto" : "Senza vendite"}</td>
                    </tr>
                  ))
              )}
            </tbody>
          </table>
          <ShowMoreToggle
            total={productIntelligence.noSalesProducts.length}
            limit={SHOPIFY_TABLE_ROW_LIMIT}
            expanded={expanded}
            onToggle={() => setExpanded((value) => !value)}
          />
        </>
      )}

      {tab === "highstock" && (
        <>
          <table className="shopify-table">
            <thead>
              <tr>
                <th>Prodotto</th>
                <th>Qty</th>
                <th>Revenue</th>
                <th>Stock</th>
                <th>Status</th>
                <th>Issue</th>
              </tr>
            </thead>
            <tbody>
              {productIntelligence.highStockLowSales.length === 0 ? (
                <tr>
                  <td colSpan={6} className="shopify-empty-copy">
                    Nessun prodotto con stock alto e vendite basse.
                  </td>
                </tr>
              ) : (
                productIntelligence.highStockLowSales
                  .slice(0, expanded ? undefined : SHOPIFY_TABLE_ROW_LIMIT)
                  .map((item) => (
                    <tr key={item.productTitle}>
                      <td>{item.productTitle}</td>
                      <td>{item.quantitySold}</td>
                      <td>—</td>
                      <td>{item.currentInventory ?? "—"}</td>
                      <td>—</td>
                      <td>{item.issue}</td>
                    </tr>
                  ))
              )}
            </tbody>
          </table>
          <ShowMoreToggle
            total={productIntelligence.highStockLowSales.length}
            limit={SHOPIFY_TABLE_ROW_LIMIT}
            expanded={expanded}
            onToggle={() => setExpanded((value) => !value)}
          />
        </>
      )}

      {tab === "seo" && (
        <>
          <table className="shopify-table">
            <thead>
              <tr>
                <th>Prodotto</th>
                <th>Qty</th>
                <th>Revenue</th>
                <th>Stock</th>
                <th>Status</th>
                <th>Issue</th>
              </tr>
            </thead>
            <tbody>
              {seoIncomplete.length === 0 ? (
                <tr>
                  <td colSpan={6} className="shopify-empty-copy">
                    Nessun prodotto fermo con SEO incompleto.
                  </td>
                </tr>
              ) : (
                seoIncomplete.slice(0, expanded ? undefined : SHOPIFY_TABLE_ROW_LIMIT).map((item) => (
                  <tr key={item.productTitle}>
                    <td>{item.productTitle}</td>
                    <td>0</td>
                    <td>{formatMoney("0")}</td>
                    <td>{item.currentInventory ?? "—"}</td>
                    <td>{item.status ?? "—"}</td>
                    <td>SEO incompleto</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <ShowMoreToggle
            total={seoIncomplete.length}
            limit={SHOPIFY_TABLE_ROW_LIMIT}
            expanded={expanded}
            onToggle={() => setExpanded((value) => !value)}
          />
        </>
      )}
    </section>
  );
}
