import { apiUrl, getApiBase, isApiBaseConfigured } from "./api";

export interface ApiDiagnosticsResult {
  apiBase: string;
  configured: boolean;
  health: "ok" | "fail" | "skipped";
  projects: "ok" | "fail" | "skipped";
  detail?: string;
}

export async function runApiDiagnostics(): Promise<ApiDiagnosticsResult> {
  const apiBase = getApiBase();
  const configured = isApiBaseConfigured();

  if (!configured) {
    return {
      apiBase: "(non configurato)",
      configured: false,
      health: "skipped",
      projects: "skipped",
      detail:
        "VITE_API_URL non configurato: imposta l'URL pubblico dell'API su Railway e rebuild WEB.",
    };
  }

  let health: "ok" | "fail" = "fail";
  let projects: "ok" | "fail" = "fail";
  let detail: string | undefined;

  try {
    const healthRes = await fetch(apiUrl("/api/health"));
    health = healthRes.ok ? "ok" : "fail";
    if (!healthRes.ok) {
      detail = `GET /api/health → ${healthRes.status}`;
    }
  } catch (err) {
    detail = err instanceof Error ? err.message : "Health check fallito";
  }

  try {
    const projectsRes = await fetch(apiUrl("/api/projects"));
    projects = projectsRes.ok ? "ok" : "fail";
    if (!projectsRes.ok) {
      const projectsDetail = `GET /api/projects → ${projectsRes.status}`;
      detail = detail ? `${detail}; ${projectsDetail}` : projectsDetail;
    }
  } catch (err) {
    const projectsDetail =
      err instanceof Error ? err.message : "Lista progetti fallita";
    detail = detail ? `${detail}; ${projectsDetail}` : projectsDetail;
  }

  return { apiBase, configured, health, projects, detail };
}
