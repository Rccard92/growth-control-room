import type { ShopifySyncResponse } from "@gcr/shared";
import { formatDurationSeconds } from "../../lib/shopify-format";

interface ShopifySyncSummaryProps {
  data: ShopifySyncResponse;
}

export function ShopifySyncSummary({ data }: ShopifySyncSummaryProps) {
  return (
    <div className="shopify-sync-summary gcr-card">
      <p className="shopify-sync-summary__title">Sync completato</p>
      <div className="shopify-sync-summary__grid">
        <div className="shopify-sync-summary__item">
          <span className="shopify-sync-summary__value">{data.productsSynced}</span>
          <span className="shopify-sync-summary__label">Prodotti</span>
        </div>
        <div className="shopify-sync-summary__item">
          <span className="shopify-sync-summary__value">{data.variantsSynced ?? 0}</span>
          <span className="shopify-sync-summary__label">Varianti</span>
        </div>
        <div className="shopify-sync-summary__item">
          <span className="shopify-sync-summary__value">{data.ordersSynced}</span>
          <span className="shopify-sync-summary__label">Ordini</span>
        </div>
        <div className="shopify-sync-summary__item">
          <span className="shopify-sync-summary__value">{data.lineItemsSynced ?? 0}</span>
          <span className="shopify-sync-summary__label">Line items</span>
        </div>
        <div className="shopify-sync-summary__item">
          <span className="shopify-sync-summary__value">
            {formatDurationSeconds(data.durationSeconds)}
          </span>
          <span className="shopify-sync-summary__label">Durata</span>
        </div>
      </div>
    </div>
  );
}
