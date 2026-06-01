import type { UserPublic } from "../models/auth";

/**
 * Token + user persistence.
 *
 * For a personal-use tool we keep tokens in localStorage so sessions survive reloads.
 * Tradeoff: localStorage is readable by any injected script (XSS). Acceptable here;
 * a multi-tenant product would use httpOnly refresh cookies + in-memory access tokens.
 */
const ACCESS_KEY = "iai.access_token";
const REFRESH_KEY = "iai.refresh_token";
const USER_KEY = "iai.user";

export const LOGOUT_EVENT = "auth:logout";

function safeGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export const session = {
  getAccessToken: (): string | null => safeGet(ACCESS_KEY),
  getRefreshToken: (): string | null => safeGet(REFRESH_KEY),

  getUser(): UserPublic | null {
    const raw = safeGet(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as UserPublic;
    } catch {
      return null;
    }
  },

  setTokens(accessToken: string, refreshToken?: string): void {
    localStorage.setItem(ACCESS_KEY, accessToken);
    if (refreshToken) localStorage.setItem(REFRESH_KEY, refreshToken);
  },

  setUser(user: UserPublic): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  clear(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
  },

  /** Notify the app (authStore listens) that the session ended unexpectedly. */
  emitLogout(): void {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event(LOGOUT_EVENT));
    }
  },
};
