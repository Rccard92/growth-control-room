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
    const detail = await response.text().catch(() => "");
    throw new Error(detail || `Richiesta fallita (${response.status})`);
  }
  return response.json() as Promise<T>;
}
