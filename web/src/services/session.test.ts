import { beforeEach, describe, expect, it } from "vitest";

import { session } from "./session";

describe("session", () => {
  beforeEach(() => localStorage.clear());

  it("stores and reads tokens", () => {
    session.setTokens("access-1", "refresh-1");
    expect(session.getAccessToken()).toBe("access-1");
    expect(session.getRefreshToken()).toBe("refresh-1");
  });

  it("keeps the existing refresh token when only access is updated", () => {
    session.setTokens("access-1", "refresh-1");
    session.setTokens("access-2");
    expect(session.getAccessToken()).toBe("access-2");
    expect(session.getRefreshToken()).toBe("refresh-1");
  });

  it("stores and reads the user", () => {
    session.setUser({ id: "u1", email: "a@b.com", display_name: "Ada" });
    expect(session.getUser()?.email).toBe("a@b.com");
  });

  it("clears everything", () => {
    session.setTokens("a", "b");
    session.setUser({ id: "u1" });
    session.clear();
    expect(session.getAccessToken()).toBeNull();
    expect(session.getUser()).toBeNull();
  });
});
