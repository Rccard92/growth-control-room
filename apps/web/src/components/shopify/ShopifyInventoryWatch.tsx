import type { ShopifyDashboardProduct } from "@gcr/shared";

interface ShopifyInventoryWatchProps {
  outOfStock: ShopifyDashboardProduct[];
  lowStock: ShopifyDashboardProduct[];
  stale: ShopifyDashboardProduct[];
}

function ProductList({
  title,
  products,
  empty,
}: {
  title: string;
  products: ShopifyDashboardProduct[];
  empty: string;
}) {
  return (
    <div className="shopify-inventory-block">
      <h4 className="shopify-inventory-block__title">{title}</h4>
      {!products.length ? (
        <p className="shopify-empty-copy">{empty}</p>
      ) : (
        <ul className="shopify-inventory-list">
          {products.slice(0, 8).map((product) => (
            <li key={`${title}-${product.title}-${product.handle ?? ""}`}>
              <span>{product.title}</span>
              <span className="shopify-inventory-list__meta">
                {product.totalInventory ?? 0} pz
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function ShopifyInventoryWatch({
  outOfStock,
  lowStock,
  stale,
}: ShopifyInventoryWatchProps) {
  return (
    <div className="shopify-panel">
      <div className="shopify-panel__header">
        <h3 className="shopify-panel__title">Inventory Watch</h3>
        <p className="shopify-panel__subtitle">Monitora scorte critiche e prodotti fermi</p>
      </div>
      <div className="shopify-inventory-grid">
        <ProductList
          title="Out of stock"
          products={outOfStock}
          empty="Nessun prodotto attivo esaurito."
        />
        <ProductList
          title="Low stock"
          products={lowStock}
          empty="Nessun prodotto con scorte basse."
        />
        <ProductList
          title="Stale products"
          products={stale}
          empty="Nessun prodotto attivo senza vendite recenti."
        />
      </div>
    </div>
  );
}
