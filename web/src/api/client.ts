import type { AccessTokenResponse } from "../models/auth";
import { session } from "../services/session";
import { endpoints } from "./endpoints";
import { ApiError } from "./errors";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";

interface RequestOptions {
  body?: unknown;
  auth?: boolean;
}

let refreshPromise: Promise<string | null> | null = null;

async function toApiError(resp: Response): Promise<ApiError> {
  let code = "error";
  let message = resp.statusText || "Request failed";
  let details: Record<string, unknown> = {};
  try {
    const data = (await resp.json()) as { error?: { code?: string; message?: string; details?: Record<string, unknown> } };
    if (data?.error) {
      code = data.error.code ?? code;
      message = data.error.message ?? message;
      details = data.error.details ?? {};
    }
  } catch {
    // non-JSON error body; keep defaults
  }
  return new ApiError(message, code, resp.status, details);
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = session.getRefreshToken();
  if (!refreshToken) return null;
  try {
    const resp = await fetch(`${BASE_URL}${endpoints.auth.refresh}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!resp.ok) return null;
    const data = (await resp.json()) as AccessTokenResponse;
    session.setTokens(data.access_token);
    return data.access_token;
  } catch {
    return null;
  }
}

async function request<T>(
  method: HttpMethod,
  path: string,
  { body, auth = true }: RequestOptions = {},
): Promise<T> {
  const send = (token: string | null): Promise<Response> => {
    const headers: Record<string, string> = {};
    if (body !== undefined) headers["content-type"] = "application/json";
    if (auth && token) headers["authorization"] = `Bearer ${token}`;
    return fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  };

  let resp = await send(auth ? session.getAccessToken() : null);

  if (resp.status === 401 && auth) {
    const newToken = await (refreshPromise ??= refreshAccessToken().finally(() => {
      refreshPromise = null;
    }));
    if (newToken) {
      resp = await send(newToken);
    }
    if (!newToken || resp.status === 401) {
      session.clear();
      session.emitLogout();
      throw await toApiError(resp);
    }
  }

  if (!resp.ok) throw await toApiError(resp);
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export const apiClient = {
  get: <T>(path: string, opts?: RequestOptions) => request<T>("GET", path, opts),
  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>("POST", path, { ...opts, body }),
  put: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>("PUT", path, { ...opts, body }),
  del: <T>(path: string, opts?: RequestOptions) => request<T>("DELETE", path, opts),
};
