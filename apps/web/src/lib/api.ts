const RAW_API_BASE = import.meta.env.VITE_API_URL ?? "";

export function getApiBase(): string {
  let base = RAW_API_BASE.trim();
  if (!base) {
    return "";
  }
  while (base.endsWith("/")) {
    base = base.slice(0, -1);
  }
  if (base.endsWith("/api")) {
    base = base.slice(0, -4);
  }
  return base;
}

export function isApiBaseConfigured(): boolean {
  return getApiBase().length > 0;
}

export function apiUrl(path: string): string {
  const base = getApiBase();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalizedPath}`;
}

function buildFetchError(path: string, status: number, text: string): Error {
  if (status === 404) {
    if (!isApiBaseConfigured()) {
      return new Error(
        "VITE_API_URL non configurato: imposta l'URL pubblico dell'API su Railway e rebuild WEB.",
      );
    }
    if (path.includes("/api/projects")) {
      return new Error(
        "Endpoint API non trovato: verifica che POST /api/projects sia attivo.",
      );
    }
    return new Error(
      "Endpoint API non trovato: verifica che POST /api/projects sia attivo.",
    );
  }

  if (text) {
    try {
      const json = JSON.parse(text) as { detail?: string };
      if (typeof json.detail === "string") {
        return new Error(json.detail);
      }
    } catch {
      // fall through to generic message
    }
  }

  return new Error(text || `Richiesta fallita (${status})`);
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  if (!isApiBaseConfigured()) {
    throw new Error(
      "VITE_API_URL non configurato: imposta l'URL pubblico dell'API su Railway e rebuild WEB.",
    );
  }

  const response = await fetch(apiUrl(path), init);
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw buildFetchError(path, response.status, text);
  }
  return response.json() as Promise<T>;
}

export async function apiUploadForm<T>(path: string, formData: FormData): Promise<T> {
  if (!isApiBaseConfigured()) {
    throw new Error(
      "VITE_API_URL non configurato: imposta l'URL pubblico dell'API su Railway e rebuild WEB.",
    );
  }

  const response = await fetch(apiUrl(path), {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw buildFetchError(path, response.status, text);
  }
  return response.json() as Promise<T>;
}
