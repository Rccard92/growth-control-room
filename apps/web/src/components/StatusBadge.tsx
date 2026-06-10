type BadgeVariant = "connected" | "not_connected" | "coming_soon" | "error" | "active";

const LABELS: Record<BadgeVariant, string> = {
  connected: "Connessa",
  not_connected: "Non connessa",
  coming_soon: "Coming soon",
  error: "Errore",
  active: "Attivo",
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
