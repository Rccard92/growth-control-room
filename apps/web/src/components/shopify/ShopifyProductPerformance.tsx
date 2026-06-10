import { useMemo, useState } from "react";
import type { ShopifyBestSeller, ShopifyDashboardProduct, ShopifySeoOpportunity } from "@gcr/shared";

interface ShopifyProductPerformanceProps {
  products: ShopifyDashboardProduct[];
  bestSellers: ShopifyBestSeller[];
  seoOpportunities: ShopifySeoOpportunity[];
}

function formatMoney(value: string, currency = "EUR"): string {
  const amount = Number(value);
  if (Number.isNaN(amount)) return value;
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function ShopifyProductPerformance({
  products,
  bestSellers,
  seoOpportunities,
}: ShopifyProductPerformanceProps) {
  const [expanded, setExpanded] = useState(false);
  const visibleProducts = expanded ? products : products.slice(0, 10);

  const sellerMap = useMemo(() => {
    const map = new Map<string, ShopifyBestSeller>();
    for (const seller of bestSellers) {
      map.set(seller.productTitle.toLowerCase(), seller);
    }
    return map;
  }, [bestSellers]);

  const seoMap = useMemo(() => {
    const map = new Map<string, ShopifySeoOpportunity[]>();
    for (const item of seoOpportunities) {
      const key = item.productTitle.toLowerCase();
      const current = map.get(key) ?? [];
      current.push(item);
      map.set(key, current);
    }
    return map;
  }, [seoOpportunities]);

  return (
    <div className="shopify-panel">
      <div className="shopify-panel__header">
        <h3 className="shopify-panel__title">Product Performance</h3>
        <p className="shopify-panel__subtitle">Catalogo, vendite e segnali SEO per prodotto</p>
      </div>
      {!products.length ? (
        <p className="shopify-empty-copy">Nessun prodotto sincronizzato.</p>
      ) : (
        <>
          <div className="shopify-table-wrap">
            <table className="shopify-table">
              <thead>
                <tr>
                  <th>Prodotto</th>
                  <th>Stato</th>
                  <th>Inventario</th>
                  <th>Vendite</th>
                  <th>SEO</th>
                </tr>
              </thead>
              <tbody>
                {visibleProducts.map((product) => {
                  const seller = sellerMap.get(product.title.toLowerCase());
                  const seoIssues = seoMap.get(product.title.toLowerCase()) ?? [];
                  return (
                    <tr key={`${product.title}-${product.handle ?? ""}`}>
                      <td>
                        <div className="shopify-product-cell">
                          {product.featuredImageUrl ? (
                            <img
                              src={product.featuredImageUrl}
                              alt=""
                              className="shopify-product-cell__thumb"
                            />
                          ) : (
                            <div className="shopify-product-cell__thumb shopify-product-cell__thumb--empty" />
                          )}
                          <div>
                            <div>{product.title}</div>
                            <div className="shopify-product-cell__meta">
                              {product.vendor ?? "—"} · {product.productType ?? "—"}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="shopify-table__pill">{product.status ?? "—"}</span>
                      </td>
                      <td>{product.totalInventory ?? "—"}</td>
                      <td>
                        {seller
                          ? `${seller.quantitySold} pz · ${formatMoney(seller.revenue)}`
                          : "—"}
                      </td>
                      <td>
                        {seoIssues.length
                          ? seoIssues.map((issue) => issue.issue).join(", ")
                          : "OK"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {products.length > 10 && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary shopify-expand-btn"
              onClick={() => setExpanded((value) => !value)}
            >
              {expanded ? "Mostra meno" : `Mostra tutti (${products.length})`}
            </button>
          )}
        </>
      )}
    </div>
  );
}
