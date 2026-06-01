export const endpoints = {
  auth: {
    register: "/auth/register",
    login: "/auth/login",
    apple: "/auth/apple",
    refresh: "/auth/refresh",
  },
  me: "/me",
  riskProfile: "/me/risk-profile",
  market: {
    search: (q: string, limit = 20) =>
      `/market/search?q=${encodeURIComponent(q)}&limit=${limit}`,
    instrument: (symbol: string) => `/market/instruments/${encodeURIComponent(symbol)}`,
    quote: (symbol: string) => `/market/quote/${encodeURIComponent(symbol)}`,
    candles: (symbol: string, resolution = "D", days = 180) =>
      `/market/candles/${encodeURIComponent(symbol)}?resolution=${resolution}&days=${days}`,
  },
  watchlist: {
    root: "/watchlist",
    items: "/watchlist/items",
    item: (instrumentId: string) => `/watchlist/items/${instrumentId}`,
  },
  portfolio: {
    root: "/portfolio",
    holdings: "/portfolio/holdings",
    holding: (id: string) => `/portfolio/holdings/${id}`,
  },
  news: (symbol: string | null, category = "company", limit = 20) => {
    const params = new URLSearchParams({ category, limit: String(limit) });
    if (symbol) params.set("symbol", symbol);
    return `/news?${params.toString()}`;
  },
  recommendations: {
    forSymbol: (symbol: string, refresh = false) =>
      `/recommendations/${encodeURIComponent(symbol)}?refresh=${refresh}`,
  },
  notifications: {
    list: (limit = 50) => `/notifications?limit=${limit}`,
    run: "/notifications/run",
    devices: "/notifications/devices",
  },
} as const;
