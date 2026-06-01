import { beforeEach, describe, expect, it } from "vitest";

import { LOGOUT_EVENT, session } from "../services/session";
import { useAuthStore } from "./authStore";

describe("authStore", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.getState().logout();
  });

  it("setSession authenticates and persists tokens", () => {
    useAuthStore.getState().setSession({ id: "u1", email: "a@b.com" }, "acc", "ref");
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAuthStore.getState().user?.email).toBe("a@b.com");
    expect(session.getAccessToken()).toBe("acc");
  });

  it("logout clears auth state and tokens", () => {
    useAuthStore.getState().setSession({ id: "u1" }, "acc", "ref");
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(session.getAccessToken()).toBeNull();
  });

  it("responds to the global logout event", () => {
    useAuthStore.getState().setSession({ id: "u1" }, "acc", "ref");
    window.dispatchEvent(new Event(LOGOUT_EVENT));
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });
});
