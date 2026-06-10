const API_BASE = import.meta.env.VITE_API_URL ?? "";

export function apiUrl(path: string): string {
  return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(apiUrl(path), init);
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    if (text) {
      try {
        const json = JSON.parse(text) as { detail?: string };
        if (typeof json.detail === "string") {
          throw new Error(json.detail);
        }
      } catch (error) {
        if (error instanceof Error && error.message !== text) {
          throw error;
        }
      }
    }
    throw new Error(text || `Richiesta fallita (${response.status})`);
  }
  return response.json() as Promise<T>;
}
