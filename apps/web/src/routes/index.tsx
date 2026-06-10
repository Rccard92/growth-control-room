import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { AiBriefPage } from "../pages/AiBriefPage";
import { ContentPage } from "../pages/ContentPage";
import { IntegrationsPage } from "../pages/IntegrationsPage";
import { LoginPage } from "../pages/LoginPage";
import { NewProjectPage } from "../pages/NewProjectPage";
import { ProjectOverviewPage } from "../pages/ProjectOverviewPage";
import { ProjectsPage } from "../pages/ProjectsPage";
import { ShopifyConnectPage } from "../pages/ShopifyConnectPage";
import { ShopifyPage } from "../pages/ShopifyPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<AppShell showSidebar={false} />}>
        <Route index element={<Navigate to="/projects" replace />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/new" element={<NewProjectPage />} />
      </Route>

      <Route path="projects/:id" element={<AppShell showSidebar />}>
        <Route index element={<ProjectOverviewPage />} />
        <Route path="integrations" element={<IntegrationsPage />} />
        <Route path="shopify" element={<ShopifyPage />} />
        <Route path="shopify/connect" element={<ShopifyConnectPage />} />
        <Route path="content" element={<ContentPage />} />
        <Route path="ai-brief" element={<AiBriefPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/projects" replace />} />
    </Routes>
  );
}
