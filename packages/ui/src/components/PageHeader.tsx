import type { ReactNode } from "react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumb?: BreadcrumbItem[];
  actions?: ReactNode;
}

export function PageHeader({ title, subtitle, breadcrumb, actions }: PageHeaderProps) {
  return (
    <header className="gcr-page-header">
      {breadcrumb && breadcrumb.length > 0 && (
        <nav className="gcr-page-header__breadcrumb" aria-label="Breadcrumb">
          {breadcrumb.map((item, index) => (
            <span key={item.label}>
              {index > 0 && " / "}
              {item.href ? <a href={item.href}>{item.label}</a> : item.label}
            </span>
          ))}
        </nav>
      )}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1 className="gcr-page-header__title">{title}</h1>
          {subtitle && <p className="gcr-page-header__subtitle">{subtitle}</p>}
        </div>
        {actions && <div>{actions}</div>}
      </div>
    </header>
  );
}
