import type { ShopifyDashboardOrder } from "@gcr/shared";

interface ShopifyRecentOrdersProps {
  orders: ShopifyDashboardOrder[];
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

function formatDate(value?: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("it-IT");
}

export function ShopifyRecentOrders({ orders }: ShopifyRecentOrdersProps) {
  return (
    <div className="shopify-panel">
      <div className="shopify-panel__header">
        <h3 className="shopify-panel__title">Recent Orders</h3>
        <p className="shopify-panel__subtitle">Ultimi ordini sincronizzati</p>
      </div>
      {!orders.length ? (
        <p className="shopify-empty-copy">Nessun ordine sincronizzato. Esegui una sync.</p>
      ) : (
        <div className="shopify-table-wrap">
          <table className="shopify-table">
            <thead>
              <tr>
                <th>Ordine</th>
                <th>Data</th>
                <th>Pagamento</th>
                <th>Fulfillment</th>
                <th style={{ textAlign: "right" }}>Totale</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order, index) => (
                <tr key={`${order.orderName ?? "order"}-${index}`}>
                  <td>{order.orderName ?? "—"}</td>
                  <td>{formatDate(order.createdAtShopify)}</td>
                  <td>
                    <span className="shopify-table__pill">{order.financialStatus ?? "—"}</span>
                  </td>
                  <td>
                    <span className="shopify-table__pill">{order.fulfillmentStatus ?? "—"}</span>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    {formatMoney(order.totalPrice, order.currency ?? "EUR")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
