import type { ContentSeoEditorialItem } from "@gcr/shared";
import {
  CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS,
  CONTENT_SEO_EDITORIAL_STATUS_LABELS,
} from "@gcr/shared";
import { EditorialStatusBadge } from "./EditorialStatusLegend";
import { getEditorialDisplayTitle } from "./editorial-display-utils";
import { formatScheduledPublishLabel } from "./editorial-publishing-utils";

interface EditorialItemCardProps {
  item: ContentSeoEditorialItem;
  onClick: () => void;
}

export function EditorialItemCard({ item, onClick }: EditorialItemCardProps) {
  const displayTitle = getEditorialDisplayTitle(item);

  return (
    <button type="button" className="editorial-item-card" onClick={onClick}>
      <span className="editorial-item-card__title" title={displayTitle}>
        {displayTitle}
      </span>
      <span className="editorial-item-card__meta">
        {CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS[item.contentType]}
      </span>
      <EditorialStatusBadge status={item.status} />
      {item.publishStatus === "scheduled" && (
        <span className="editorial-item-card__scheduled">
          {formatScheduledPublishLabel(item.scheduledPublishAt)}
        </span>
      )}
      <span className="editorial-item-card__status-label">
        {CONTENT_SEO_EDITORIAL_STATUS_LABELS[item.status]}
      </span>
      {item.linkedShopifyProductTitle && (
        <span className="editorial-item-card__product">{item.linkedShopifyProductTitle}</span>
      )}
    </button>
  );
}
