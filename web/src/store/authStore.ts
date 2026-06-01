import { create } from "zustand";

import type { UserPublic } from "../models/auth";
import { LOGOUT_EVENT, session } from "../services/session";

interface AuthState {
  user: UserPublic | null;
  isAuthenticated: boolean;
  setSession: (user: UserPublic, accessToken: string, refreshToken: string) => void;
  setUser: (user: UserPublic) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: session.getUser(),
  isAuthenticated: Boolean(session.getAccessToken()),

  setSession: (user, accessToken, refreshToken) => {
    session.setTokens(accessToken, refreshToken);
    session.setUser(user);
    set({ user, isAuthenticated: true });
  },

  setUser: (user) => {
    session.setUser(user);
    set({ user });
  },

  logout: () => {
    session.clear();
    set({ user: null, isAuthenticated: false });
  },
}));

// The API client emits this when a refresh fails — force the app back to logged-out.
if (typeof window !== "undefined") {
  window.addEventListener(LOGOUT_EVENT, () => {
    useAuthStore.getState().logout();
  });
}
