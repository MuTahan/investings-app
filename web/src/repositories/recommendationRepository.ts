import { apiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type { RecommendationDetail } from "../models/recommendation";

export const recommendationRepository = {
  forSymbol: (symbol: string, refresh = false) =>
    apiClient.get<RecommendationDetail>(endpoints.recommendations.forSymbol(symbol, refresh)),
};
