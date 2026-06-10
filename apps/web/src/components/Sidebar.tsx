import { NavLink, useParams } from "react-router-dom";
import { useProject } from "../hooks/useProjects";
import { PROJECT_NAV } from "../routes/config";

export function Sidebar() {
  const { id } = useParams<{ id: string }>();
  const { data: project } = useProject(id);

  if (!id) return null;

  return (
    <aside className="gcr-sidebar">
      <p className="gcr-sidebar__title">Progetto</p>
      <p className="gcr-sidebar__project-name">{project?.name ?? id.slice(0, 8)}</p>
      <nav>
        {PROJECT_NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={"end" in item ? item.end : undefined}
            className={({ isActive }) =>
              `gcr-sidebar__link${isActive ? " active" : ""}`
            }
          >
            <span className="gcr-sidebar__icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
