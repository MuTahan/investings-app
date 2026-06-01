import { apiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type { Watchlist } from "../models/portfolio";

interface MessageResponse {
  message: string;
}

export const watchlistRepository = {
  get: () => apiClient.get<Watchlist>(endpoints.watchlist.root),

  addItem: (symbol: string) =>
    apiClient.post<MessageResponse>(endpoints.watchlist.items, { symbol }),

  removeItem: (instrumentId: string) =>
    apiClient.del<void>(endpoints.watchlist.item(instrumentId)),
};
