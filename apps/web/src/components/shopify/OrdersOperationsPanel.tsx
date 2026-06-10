import { useState } from "react";
import type { ShopifyDashboardOrder, ShopifyOrdersSection } from "@gcr/shared";
import { SHOPIFY_TABLE_ROW_LIMIT, sliceWithLimit } from "../../lib/shopify-dashboard-blocks";
import { formatShopifyDate } from "../../lib/shopify-format";
import { ShowMoreToggle } from "./ShowMoreToggle";

interface OrdersOperationsPanelProps {
  orderOperations: ShopifyOrdersSection;
  formatMoney: (value: string, currency?: string | null) => string;
}

type OrderTab = "recent" | "pending" | "unfulfilled";

const TABS: { id: OrderTab; label: string }[] = [
  { id: "recent", label: "Recenti" },
  { id: "pending", label: "Pending" },
  { id: "unfulfilled", label: "Unfulfilled" },
];

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
      <td>{formatShopifyDate(order.createdAtShopify)}</td>
      <td>{order.financialStatus ?? "—"}</td>
      <td>{order.fulfillmentStatus ?? "—"}</td>
      <td>{formatMoney(order.totalPrice, order.currency)}</td>
    </tr>
  );
}

export function OrdersOperationsPanel({ orderOperations, formatMoney }: OrdersOperationsPanelProps) {
  const [tab, setTab] = useState<OrderTab>("recent");
  const [expanded, setExpanded] = useState(false);

  const ordersByTab = {
    recent: orderOperations.recentOrders,
    pending: orderOperations.pendingOrders,
    unfulfilled: orderOperations.unfulfilledOrders,
  }[tab];

  const visibleOrders = sliceWithLimit(ordersByTab, SHOPIFY_TABLE_ROW_LIMIT, expanded);

  return (
    <section className="shopify-orders-ops gcr-card">
      <h3 className="shopify-panel__title">Orders Operations</h3>
      <div className="shopify-orders-ops__badges">
        {orderOperations.pendingOrders.length > 0 && (
          <span className="shopify-severity shopify-severity--warning">
            {orderOperations.pendingOrders.length} pending
          </span>
        )}
        {orderOperations.unfulfilledOrders.length > 0 && (
          <span className="shopify-severity shopify-severity--warning">
            {orderOperations.unfulfilledOrders.length} unfulfilled
          </span>
        )}
      </div>

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
          {visibleOrders.length === 0 ? (
            <tr>
              <td colSpan={5} className="shopify-empty-copy">
                Nessun ordine in questa sezione.
              </td>
            </tr>
          ) : (
            visibleOrders.map((order) => (
              <OrderRow
                key={`${order.orderName}-${order.createdAtShopify}`}
                order={order}
                formatMoney={formatMoney}
              />
            ))
          )}
        </tbody>
      </table>
      <ShowMoreToggle
        total={ordersByTab.length}
        limit={SHOPIFY_TABLE_ROW_LIMIT}
        expanded={expanded}
        onToggle={() => setExpanded((value) => !value)}
      />
    </section>
  );
}
