import { apiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type { RecommendationCenter, RecommendationDetail } from "../models/recommendation";

export const recommendationRepository = {
  forSymbol: (symbol: string, refresh = false) =>
    apiClient.get<RecommendationDetail>(endpoints.recommendations.forSymbol(symbol, refresh)),

  center: (params: Record<string, string> = {}) =>
    apiClient.get<RecommendationCenter>(endpoints.recommendations.center(params)),
};
