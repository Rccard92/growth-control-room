import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, UnauthorizedError } from "./api";
import { getStoredToken, setStoredToken } from "./auth-api";

const originalFetch = globalThis.fetch;

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("authenticated api client", () => {
  beforeEach(() => {
    setStoredToken(null);
    vi.stubEnv("VITE_API_URL", "https://api.example.com");
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    setStoredToken(null);
    vi.unstubAllEnvs();
  });

  it("sends the bearer token when a session exists", async () => {
    setStoredToken("tok-123");
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await apiFetch("/api/projects");

    const headers = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer tok-123");
  });

  it("omits the header when there is no session", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await apiFetch("/api/projects");

    const init = fetchMock.mock.calls[0][1] ?? {};
    expect((init.headers ?? {}).Authorization).toBeUndefined();
  });

  it("clears the token and throws UnauthorizedError on 401", async () => {
    setStoredToken("tok-scaduto");
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: "no" }, 401)) as unknown as typeof fetch;

    await expect(apiFetch("/api/projects")).rejects.toBeInstanceOf(UnauthorizedError);
    expect(getStoredToken()).toBeNull();
  });

  it("keeps a failed login as a normal error, not a session expiry", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(
        jsonResponse({ detail: "Email o password non corretti." }, 401),
      ) as unknown as typeof fetch;

    await expect(apiFetch("/api/auth/login", { method: "POST" })).rejects.not.toBeInstanceOf(
      UnauthorizedError,
    );
  });
});
