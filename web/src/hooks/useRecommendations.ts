import { useQuery } from "@tanstack/react-query";

import { recommendationRepository } from "../repositories/recommendationRepository";

export function useRecommendation(symbol: string | undefined, refresh = false) {
  return useQuery({
    queryKey: ["recommendation", symbol, refresh],
    queryFn: () => recommendationRepository.forSymbol(symbol as string, refresh),
    enabled: Boolean(symbol),
    retry: false,
  });
}

export function useRecommendationCenter(filters: Record<string, string> = {}) {
  return useQuery({
    queryKey: ["recommendation-center", filters],
    queryFn: () => recommendationRepository.center(filters),
  });
}
