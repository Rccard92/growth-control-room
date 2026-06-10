import { NavLink, Outlet, useParams } from "react-router-dom";

const PROJECT_NAV = [
  { to: "", label: "Panoramica", end: true },
  { to: "integrations", label: "Integrazioni" },
  { to: "shopify", label: "Shopify" },
  { to: "content", label: "Contenuti" },
  { to: "ai-brief", label: "AI Brief" },
] as const;

export function ProjectLayout() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="project-layout">
      <aside className="project-layout__sidebar">
        <p className="project-layout__sidebar-title">Progetto {id}</p>
        <nav className="project-layout__nav">
          {PROJECT_NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? "active" : undefined)}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="project-layout__content">
        <Outlet />
      </div>
    </div>
  );
}
