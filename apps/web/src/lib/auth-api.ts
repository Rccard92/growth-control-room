import { apiFetch, jsonBody } from "./api";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  lastLoginAt: string | null;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  expiresAt: string;
  user: AuthUser;
}

const TOKEN_STORAGE_KEY = "gcr.auth.token";

let inMemoryToken: string | null = null;
const listeners = new Set<(token: string | null) => void>();

export function getStoredToken(): string | null {
  if (inMemoryToken !== null) return inMemoryToken;
  try {
    inMemoryToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    // private mode or blocked storage: the session simply does not survive a reload
    inMemoryToken = null;
  }
  return inMemoryToken;
}

export function setStoredToken(token: string | null): void {
  inMemoryToken = token;
  try {
    if (token) {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  } catch {
    // ignore: the in-memory token still works for this tab
  }
  listeners.forEach((listener) => listener(token));
}

export function onTokenChange(listener: (token: string | null) => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await apiFetch<LoginResponse>("/api/auth/login", {
    method: "POST",
    ...jsonBody({ email, password }),
  });
  setStoredToken(response.accessToken);
  return response;
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  return apiFetch<AuthUser>("/api/auth/me");
}

export async function logout(): Promise<void> {
  try {
    await apiFetch<void>("/api/auth/logout", { method: "POST" });
  } finally {
    setStoredToken(null);
  }
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  await apiFetch<void>("/api/auth/change-password", {
    method: "POST",
    ...jsonBody({ currentPassword, newPassword }),
  });
  setStoredToken(null);
}
