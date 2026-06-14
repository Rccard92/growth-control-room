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
      const json = JSON.parse(text) as {
        detail?: string | Array<{ loc?: unknown[]; msg?: string; input?: unknown }>;
      };
      if (typeof json.detail === "string") {
        return new Error(json.detail);
      }
      if (status === 422 && Array.isArray(json.detail) && json.detail.length > 0) {
        const bodyError = json.detail.find(
          (item) => Array.isArray(item.loc) && item.loc[0] === "body",
        );
        if (
          path.includes("ai-model-settings")
          && bodyError
          && typeof bodyError.input === "string"
          && bodyError.input.trim().startsWith("{")
        ) {
          return new Error("Errore salvataggio modello: payload non valido");
        }
        const firstMsg = json.detail.find((item) => typeof item.msg === "string")?.msg;
        if (firstMsg) {
          return new Error(firstMsg);
        }
      }
    } catch {
      // fall through to generic message
    }
  }

  return new Error(text || `Richiesta fallita (${status})`);
}

export function formatAiErrorMessage(err: unknown, fallback = "Generazione AI non riuscita."): string {
  const raw = err instanceof Error ? err.message : fallback;
  if (!raw.trim()) return fallback;
  if (raw.startsWith("Errore AI:")) return raw;
  if (
    raw.toLowerCase().includes("modello")
    || raw.toLowerCase().includes("openai")
    || raw.toLowerCase().includes("parametr")
    || raw.toLowerCase().includes("api key")
  ) {
    return raw.startsWith("Errore") ? raw : `Errore AI: ${raw}`;
  }
  return raw;
}

export function jsonBody(data: unknown): Pick<RequestInit, "body" | "headers"> {
  return {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  };
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
