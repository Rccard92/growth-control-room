import { Link } from "react-router-dom";
import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumb?: { label: string; href?: string }[];
  actions?: ReactNode;
}

export function PageHeader({ title, subtitle, breadcrumb, actions }: PageHeaderProps) {
  return (
    <header className="gcr-page-header">
      {breadcrumb && breadcrumb.length > 0 && (
        <nav className="gcr-page-header__breadcrumb" aria-label="Breadcrumb">
          {breadcrumb.map((item, index) => (
            <span key={`${item.label}-${index}`}>
              {index > 0 && " / "}
              {item.href ? <Link to={item.href}>{item.label}</Link> : item.label}
            </span>
          ))}
        </nav>
      )}
      <div className="gcr-page-header__row">
        <div>
          <h1 className="gcr-page-header__title">{title}</h1>
          {subtitle && <p className="gcr-page-header__subtitle">{subtitle}</p>}
        </div>
        {actions && <div className="gcr-page-header__actions">{actions}</div>}
      </div>
    </header>
  );
}
