import type { ReactNode } from "react";

export interface CardProps {
  title?: string;
  description?: string;
  children?: ReactNode;
  className?: string;
}

export function Card({ title, description, children, className = "" }: CardProps) {
  return (
    <div className={`gcr-card ${className}`.trim()}>
      {title && <h3 className="gcr-card__title">{title}</h3>}
      {description && <p className="gcr-card__description">{description}</p>}
      {children}
    </div>
  );
}
