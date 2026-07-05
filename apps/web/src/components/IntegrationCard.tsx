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
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
  secondaryHref?: string;
  secondaryDisabled?: boolean;
  detailText?: string;
}

function toBadgeVariant(status: IntegrationUiStatus): Parameters<typeof StatusBadge>[0]["variant"] {
  if (status === "coming_soon") {
    return "coming_soon";
  }
  return status;
}

function renderActionButton(
  label: string,
  options: {
    disabled?: boolean;
    href?: string;
    onAction?: () => void;
    className?: string;
  },
) {
  const className = options.className ?? "gcr-btn gcr-btn--secondary";
  if (options.disabled) {
    return (
      <button type="button" className={className} disabled>
        {label}
      </button>
    );
  }
  if (options.href) {
    return (
      <Link to={options.href} className={className}>
        {label}
      </Link>
    );
  }
  if (options.onAction) {
    return (
      <button type="button" className={className} onClick={options.onAction}>
        {label}
      </button>
    );
  }
  return null;
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
  secondaryActionLabel,
  onSecondaryAction,
  secondaryHref,
  secondaryDisabled = false,
  detailText,
}: IntegrationCardProps) {
  const brandIcon = INTEGRATION_BRAND_ICONS[meta.provider];

  const primaryAction =
    actionLabel == null
      ? null
      : renderActionButton(actionLabel, {
          disabled,
          href,
          onAction,
        });

  const secondaryAction =
    secondaryActionLabel == null
      ? null
      : renderActionButton(secondaryActionLabel, {
          disabled: secondaryDisabled,
          href: secondaryHref,
          onAction: onSecondaryAction,
          className: "gcr-btn gcr-btn--secondary integration-card__secondary-action",
        });

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
      {detailText && <p className="integration-card__detail">{detailText}</p>}
      {(primaryAction || secondaryAction) && (
        <div className="integration-card__actions">
          {primaryAction}
          {secondaryAction}
        </div>
      )}
    </div>
  );
}
