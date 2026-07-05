type BadgeVariant =
  | "connected"
  | "not_connected"
  | "coming_soon"
  | "error"
  | "active"
  | "needs_setup"
  | "needs_reconnect"
  | "missing_credentials"
  | "setup_incomplete";

const LABELS: Record<BadgeVariant, string> = {
  connected: "Connessa",
  not_connected: "Non connessa",
  coming_soon: "Coming soon",
  error: "Errore",
  active: "Attivo",
  needs_setup: "Da collegare",
  needs_reconnect: "Da ricollegare",
  missing_credentials: "Mancante",
  setup_incomplete: "Setup incompleto",
};

interface StatusBadgeProps {
  variant: BadgeVariant;
  label?: string;
}

export function StatusBadge({ variant, label }: StatusBadgeProps) {
  return (
    <span className={`gcr-badge gcr-badge--${variant}`}>
      {label ?? LABELS[variant]}
    </span>
  );
}

export type { BadgeVariant };
