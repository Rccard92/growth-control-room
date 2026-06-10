import { NavLink, Outlet } from "react-router-dom";

export function AppLayout() {
  return (
    <div className="app-layout">
      <header className="app-layout__header">
        <NavLink to="/projects" className="app-layout__logo">
          Growth Control Room
        </NavLink>
        <nav className="app-layout__nav">
          <NavLink to="/projects">Progetti</NavLink>
          <NavLink to="/login">Login</NavLink>
        </nav>
      </header>
      <main className="app-layout__main">
        <Outlet />
      </main>
    </div>
  );
}
