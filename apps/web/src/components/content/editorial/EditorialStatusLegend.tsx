import type { ContentSeoEditorialStatus } from "@gcr/shared";
import { CONTENT_SEO_EDITORIAL_STATUS_LABELS } from "@gcr/shared";

const STATUS_CLASS: Record<ContentSeoEditorialStatus, string> = {
  idea: "editorial-status--idea",
  brief_pending: "editorial-status--brief-pending",
  brief_approved: "editorial-status--brief-approved",
  draft_pending: "editorial-status--draft-pending",
  draft_review: "editorial-status--draft-review",
  ready_to_publish: "editorial-status--ready",
  scheduled: "editorial-status--scheduled",
  published: "editorial-status--published",
  publish_error: "editorial-status--error",
};

interface EditorialStatusBadgeProps {
  status: ContentSeoEditorialStatus;
}

export function EditorialStatusBadge({ status }: EditorialStatusBadgeProps) {
  return (
    <span className={`editorial-status ${STATUS_CLASS[status]}`}>
      {CONTENT_SEO_EDITORIAL_STATUS_LABELS[status]}
    </span>
  );
}

export function EditorialStatusLegend() {
  const entries = Object.entries(CONTENT_SEO_EDITORIAL_STATUS_LABELS) as [
    ContentSeoEditorialStatus,
    string,
  ][];
  return (
    <div className="editorial-legend">
      <span className="editorial-legend__title">Stati</span>
      <div className="editorial-legend__items">
        {entries.map(([status, label]) => (
          <span key={status} className="editorial-legend__item">
            <EditorialStatusBadge status={status} />
            <span className="editorial-legend__label">{label}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
