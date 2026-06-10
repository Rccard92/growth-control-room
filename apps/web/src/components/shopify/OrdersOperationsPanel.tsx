import type { ShopifyDashboardOrder, ShopifyOrdersSection } from "@gcr/shared";

interface OrdersOperationsPanelProps {
  orders: ShopifyOrdersSection;
  formatMoney: (value: string, currency?: string | null) => string;
}

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("it-IT", { dateStyle: "short" }).format(date);
}

function isPending(order: ShopifyDashboardOrder): boolean {
  const status = (order.financialStatus ?? "").toUpperCase();
  return status === "PENDING" || status === "AUTHORIZED" || status === "PARTIALLY_PAID";
}

function isUnfulfilled(order: ShopifyDashboardOrder): boolean {
  const status = (order.fulfillmentStatus ?? "").toUpperCase();
  return status !== "FULFILLED" && status !== "";
}

function OrderRow({
  order,
  formatMoney,
}: {
  order: ShopifyDashboardOrder;
  formatMoney: (value: string, currency?: string | null) => string;
}) {
  const pending = isPending(order);
  const unfulfilled = isUnfulfilled(order);
  const rowClass = pending
    ? "shopify-order-row--pending"
    : unfulfilled
      ? "shopify-order-row--unfulfilled"
      : "";

  return (
    <tr className={rowClass}>
      <td>{order.orderName ?? "—"}</td>
      <td>{formatDate(order.createdAtShopify)}</td>
      <td>{order.financialStatus ?? "—"}</td>
      <td>{order.fulfillmentStatus ?? "—"}</td>
      <td>{formatMoney(order.totalPrice, order.currency)}</td>
    </tr>
  );
}

export function OrdersOperationsPanel({ orders, formatMoney }: OrdersOperationsPanelProps) {
  const displayOrders = orders.recentOrders.length > 0 ? orders.recentOrders : [];

  return (
    <section className="shopify-orders-ops gcr-card">
      <h3 className="shopify-panel__title">Orders Operations</h3>
      <div className="shopify-orders-ops__badges">
        {orders.pendingOrders.length > 0 && (
          <span className="shopify-severity shopify-severity--warning">
            {orders.pendingOrders.length} pending
          </span>
        )}
        {orders.unfulfilledOrders.length > 0 && (
          <span className="shopify-severity shopify-severity--warning">
            {orders.unfulfilledOrders.length} unfulfilled
          </span>
        )}
      </div>
      <table className="shopify-table">
        <thead>
          <tr>
            <th>Ordine</th>
            <th>Data</th>
            <th>Pagamento</th>
            <th>Fulfillment</th>
            <th>Totale</th>
          </tr>
        </thead>
        <tbody>
          {displayOrders.length === 0 ? (
            <tr>
              <td colSpan={5} className="shopify-empty-copy">
                Nessun ordine sincronizzato.
              </td>
            </tr>
          ) : (
            displayOrders.map((order) => (
              <OrderRow
                key={`${order.orderName}-${order.createdAtShopify}`}
                order={order}
                formatMoney={formatMoney}
              />
            ))
          )}
        </tbody>
      </table>
    </section>
  );
}
