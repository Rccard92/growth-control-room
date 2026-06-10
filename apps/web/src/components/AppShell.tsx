import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

interface AppShellProps {
  showSidebar?: boolean;
}

export function AppShell({ showSidebar = false }: AppShellProps) {
  return (
    <div className="gcr-shell">
      <Topbar />
      <div className="gcr-shell__body">
        {showSidebar && <Sidebar />}
        <main className="gcr-shell__main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
