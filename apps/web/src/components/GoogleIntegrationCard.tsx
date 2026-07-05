import type { GoogleServiceStatus } from "@gcr/shared";

interface GoogleIntegrationCardProps {
  title: string;
  description: string;
  icon: string;
  status: GoogleServiceStatus;
  actionLabel?: string;
  onAction?: () => void;
  disabled?: boolean;
  note?: string;
}

function getStatusLabel(status: GoogleServiceStatus): string {
  switch (status.status) {
    case "connected":
      return "Configurata";
    case "needs_setup":
      return "Da collegare";
    case "missing_credentials":
      return "Mancante";
    case "setup_incomplete":
      return "Setup incompleto";
    default:
      return "Non connessa";
  }
}

function getStatusClass(status: GoogleServiceStatus): string {
  switch (status.status) {
    case "connected":
      return "google-integration-card__badge--connected";
    case "needs_setup":
      return "google-integration-card__badge--needs-setup";
    case "setup_incomplete":
      return "google-integration-card__badge--setup-incomplete";
    default:
      return "google-integration-card__badge--missing";
  }
}

export function GoogleIntegrationCard({
  title,
  description,
  icon,
  status,
  actionLabel,
  onAction,
  disabled = false,
  note,
}: GoogleIntegrationCardProps) {
  return (
    <div className="google-integration-card gcr-card">
      <div className="google-integration-card__header">
        <span className="google-integration-card__icon" aria-hidden>
          {icon}
        </span>
        <span className={`google-integration-card__badge ${getStatusClass(status)}`}>
          {getStatusLabel(status)}
        </span>
      </div>
      <h3 className="google-integration-card__title">{title}</h3>
      <p className="google-integration-card__description">{description}</p>
      {status.message && (
        <p className="google-integration-card__message">{status.message}</p>
      )}
      {note && <p className="google-integration-card__note">{note}</p>}
      {actionLabel && onAction && status.status !== "connected" && (
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary"
          disabled={disabled}
          onClick={onAction}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
