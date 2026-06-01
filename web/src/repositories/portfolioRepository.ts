import { apiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type { Portfolio } from "../models/portfolio";

interface MessageResponse {
  message: string;
}

export interface AddHoldingPayload {
  symbol: string;
  quantity: number;
  avg_cost: number;
}

export interface UpdateHoldingPayload {
  quantity: number;
  avg_cost: number;
}

export const portfolioRepository = {
  get: () => apiClient.get<Portfolio>(endpoints.portfolio.root),

  addHolding: (payload: AddHoldingPayload) =>
    apiClient.post<MessageResponse>(endpoints.portfolio.holdings, payload),

  updateHolding: (id: string, payload: UpdateHoldingPayload) =>
    apiClient.put<MessageResponse>(endpoints.portfolio.holding(id), payload),

  deleteHolding: (id: string) => apiClient.del<void>(endpoints.portfolio.holding(id)),
};
