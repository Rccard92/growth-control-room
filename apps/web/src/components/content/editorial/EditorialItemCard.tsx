import type { ContentSeoEditorialItem } from "@gcr/shared";
import {
  CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS,
} from "@gcr/shared";
import { EditorialStatusBadge } from "./EditorialStatusLegend";

interface EditorialItemCardProps {
  item: ContentSeoEditorialItem;
  onClick: () => void;
}

export function EditorialItemCard({ item, onClick }: EditorialItemCardProps) {
  return (
    <button type="button" className="editorial-item-card" onClick={onClick}>
      <span className="editorial-item-card__title">{item.title}</span>
      <span className="editorial-item-card__meta">
        {CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS[item.contentType]}
      </span>
      <EditorialStatusBadge status={item.status} />
      {item.linkedShopifyProductTitle && (
        <span className="editorial-item-card__product">{item.linkedShopifyProductTitle}</span>
      )}
    </button>
  );
}
