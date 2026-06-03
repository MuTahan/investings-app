import type { ReactNode } from "react";
import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { LoginPage } from "./features/auth/LoginPage";
import { RegisterPage } from "./features/auth/RegisterPage";
import { ChatPage } from "./features/chat/ChatPage";
import { InstrumentDetailPage } from "./features/markets/InstrumentDetailPage";
import { MarketsPage } from "./features/markets/MarketsPage";
import { NotificationsPage } from "./features/notifications/NotificationsPage";
import { PortfolioPage } from "./features/portfolio/PortfolioPage";
import { RecommendationCenterPage } from "./features/recommendations/RecommendationCenterPage";
import { RecommendationPage } from "./features/recommendations/RecommendationPage";
import { SettingsPage } from "./features/settings/SettingsPage";
import { WatchlistPage } from "./features/watchlist/WatchlistPage";
import { useAuthStore } from "./store/authStore";

function RequireAuth() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

function PublicOnly({ children }: { children: ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <Navigate to="/" replace /> : <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: (
      <PublicOnly>
        <LoginPage />
      </PublicOnly>
    ),
  },
  {
    path: "/register",
    element: (
      <PublicOnly>
        <RegisterPage />
      </PublicOnly>
    ),
  },
  {
    element: <RequireAuth />,
    children: [
      { path: "/", element: <MarketsPage /> },
      { path: "/markets/:symbol", element: <InstrumentDetailPage /> },
      { path: "/watchlist", element: <WatchlistPage /> },
      { path: "/portfolio", element: <PortfolioPage /> },
      { path: "/recommendations", element: <RecommendationCenterPage /> },
      { path: "/chat", element: <ChatPage /> },
      { path: "/notifications", element: <NotificationsPage /> },
      { path: "/recommendations/:symbol", element: <RecommendationPage /> },
      { path: "/settings", element: <SettingsPage /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
