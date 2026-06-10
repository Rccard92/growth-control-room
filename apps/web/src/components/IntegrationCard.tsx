import { Link } from "react-router-dom";
import type { IntegrationMeta, IntegrationStatus } from "@gcr/shared";
import { StatusBadge } from "./StatusBadge";

interface IntegrationCardProps {
  meta: IntegrationMeta;
  status: IntegrationStatus | "coming_soon";
  href?: string;
  onAction?: () => void;
  actionLabel: string;
  disabled?: boolean;
}

export function IntegrationCard({
  meta,
  status,
  href,
  actionLabel,
  disabled = false,
}: IntegrationCardProps) {
  const badgeVariant =
    status === "coming_soon" ? "coming_soon" : status;

  const action = disabled ? (
    <button type="button" className="gcr-btn gcr-btn--secondary" disabled>
      {actionLabel}
    </button>
  ) : href ? (
    <Link to={href} className="gcr-btn gcr-btn--secondary">
      {actionLabel}
    </Link>
  ) : null;

  return (
    <div className="gcr-card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
        <span style={{ fontSize: "1.5rem" }}>{meta.icon}</span>
        <StatusBadge variant={badgeVariant} />
      </div>
      <h3 className="gcr-card__title">{meta.label}</h3>
      <p className="gcr-card__description">{meta.description}</p>
      {action}
    </div>
  );
}
