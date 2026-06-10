import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: string;
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ icon = "◌", title, description, action }: EmptyStateProps) {
  return (
    <div className="gcr-empty">
      <div className="gcr-empty__icon">{icon}</div>
      <h2 className="gcr-empty__title">{title}</h2>
      <p className="gcr-empty__text">{description}</p>
      {action}
    </div>
  );
}
