import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { session } from "../services/session";
import { apiClient } from "./client";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("apiClient", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("attaches the bearer token and returns parsed JSON", async () => {
    session.setTokens("access-1", "refresh-1");
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    const data = await apiClient.get<{ ok: boolean }>("/x");

    expect(data).toEqual({ ok: true });
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>).authorization).toBe("Bearer access-1");
  });

  it("refreshes the access token on 401 then retries the request", async () => {
    session.setTokens("expired", "refresh-1");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ error: { code: "unauthorized", message: "x" } }, 401))
      .mockResolvedValueOnce(jsonResponse({ access_token: "new-access" }, 200))
      .mockResolvedValueOnce(jsonResponse({ ok: true }, 200));
    vi.stubGlobal("fetch", fetchMock);

    const data = await apiClient.get<{ ok: boolean }>("/y");

    expect(data).toEqual({ ok: true });
    expect(session.getAccessToken()).toBe("new-access");
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("clears the session and emits logout when refresh fails", async () => {
    session.setTokens("expired", "refresh-1");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ error: { code: "unauthorized", message: "x" } }, 401))
      .mockResolvedValueOnce(jsonResponse({ error: { code: "unauthorized" } }, 401));
    vi.stubGlobal("fetch", fetchMock);
    const onLogout = vi.fn();
    window.addEventListener("auth:logout", onLogout);

    await expect(apiClient.get("/z")).rejects.toMatchObject({ status: 401 });

    expect(onLogout).toHaveBeenCalledTimes(1);
    expect(session.getAccessToken()).toBeNull();
    window.removeEventListener("auth:logout", onLogout);
  });
});
