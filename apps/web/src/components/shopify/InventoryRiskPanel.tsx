import { useState } from "react";
import type { ShopifyInventorySection } from "@gcr/shared";
import { SHOPIFY_TABLE_ROW_LIMIT, sliceWithLimit } from "../../lib/shopify-dashboard-blocks";
import { ShowMoreToggle } from "./ShowMoreToggle";

interface InventoryRiskPanelProps {
  inventoryRisk: ShopifyInventorySection;
}

export function InventoryRiskPanel({ inventoryRisk }: InventoryRiskPanelProps) {
  const { inventorySummary, outOfStockProducts, lowStockProducts } = inventoryRisk;
  const urgent = [...outOfStockProducts, ...lowStockProducts];
  const [expanded, setExpanded] = useState(false);
  const visibleItems = sliceWithLimit(urgent, SHOPIFY_TABLE_ROW_LIMIT, expanded);

  return (
    <section className="shopify-inventory-risk gcr-card">
      <h3 className="shopify-panel__title">Inventory Risk</h3>

      <div className="shopify-inventory-summary">
        <div className="shopify-inventory-summary__item">
          <span className="shopify-inventory-summary__value">{inventorySummary.totalUnits}</span>
          <span className="shopify-inventory-summary__label">Unità totali</span>
        </div>
        <div className="shopify-inventory-summary__item">
          <span className="shopify-inventory-summary__value">{inventorySummary.activeProducts}</span>
          <span className="shopify-inventory-summary__label">Attivi</span>
        </div>
        <div className="shopify-inventory-summary__item shopify-inventory-summary__item--critical">
          <span className="shopify-inventory-summary__value">
            {inventorySummary.zeroStockActiveProducts}
          </span>
          <span className="shopify-inventory-summary__label">Out of stock</span>
        </div>
        <div className="shopify-inventory-summary__item">
          <span className="shopify-inventory-summary__value">
            {inventorySummary.lowStockActiveProducts}
          </span>
          <span className="shopify-inventory-summary__label">Scorte basse</span>
        </div>
      </div>

      <h4 className="shopify-panel__subtitle">Da controllare subito</h4>
      {urgent.length === 0 ? (
        <p className="shopify-empty-copy">Nessun rischio inventario rilevato.</p>
      ) : (
        <>
          <ul className="shopify-inventory-list">
            {visibleItems.map((product) => (
              <li key={product.title} className="shopify-inventory-list__item">
                <span className="shopify-inventory-list__title">{product.title}</span>
                <span
                  className={`shopify-severity ${
                    product.totalInventory === 0
                      ? "shopify-severity--critical"
                      : "shopify-severity--warning"
                  }`}
                >
                  {product.totalInventory === 0
                    ? "Out of stock"
                    : `${product.totalInventory} unità`}
                </span>
              </li>
            ))}
          </ul>
          <ShowMoreToggle
            total={urgent.length}
            limit={SHOPIFY_TABLE_ROW_LIMIT}
            expanded={expanded}
            onToggle={() => setExpanded((value) => !value)}
          />
        </>
      )}
    </section>
  );
}
