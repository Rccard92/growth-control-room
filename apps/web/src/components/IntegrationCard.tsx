import { Link } from "react-router-dom";
import type { IntegrationMeta, IntegrationUiStatus } from "@gcr/shared";
import { INTEGRATION_BRAND_ICONS } from "./integrationBrandIcons";
import { StatusBadge } from "./StatusBadge";

export interface IntegrationCardProps {
  meta: IntegrationMeta;
  status: IntegrationUiStatus;
  href?: string;
  onAction?: () => void;
  actionLabel?: string;
  disabled?: boolean;
  note?: string;
  badgeLabel?: string;
}

function toBadgeVariant(status: IntegrationUiStatus): Parameters<typeof StatusBadge>[0]["variant"] {
  if (status === "coming_soon") {
    return "coming_soon";
  }
  return status;
}

export function IntegrationCard({
  meta,
  status,
  href,
  onAction,
  actionLabel,
  disabled = false,
  note,
  badgeLabel,
}: IntegrationCardProps) {
  const brandIcon = INTEGRATION_BRAND_ICONS[meta.provider];

  const action =
    actionLabel == null ? null : disabled ? (
      <button type="button" className="gcr-btn gcr-btn--secondary" disabled>
        {actionLabel}
      </button>
    ) : href ? (
      <Link to={href} className="gcr-btn gcr-btn--secondary">
        {actionLabel}
      </Link>
    ) : onAction ? (
      <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onAction}>
        {actionLabel}
      </button>
    ) : null;

  return (
    <div className="gcr-card">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "0.75rem",
        }}
      >
        {brandIcon ? (
          <span className="integration-card__brand-icon">
            <img src={brandIcon} alt="" aria-hidden="true" />
          </span>
        ) : (
          <span className="integration-card__emoji-icon">{meta.icon}</span>
        )}
        <StatusBadge variant={toBadgeVariant(status)} label={badgeLabel} />
      </div>
      <h3 className="gcr-card__title">{meta.label}</h3>
      <p className="gcr-card__description">{meta.description}</p>
      {note && <p className="integration-card__note">{note}</p>}
      {action}
    </div>
  );
}
