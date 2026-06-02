import { useQuery } from "@tanstack/react-query";

import { newsRepository } from "../repositories/newsRepository";

export function useNews(symbol: string | null, category = "company") {
  return useQuery({
    queryKey: ["news", symbol, category],
    queryFn: () => newsRepository.list(symbol, category),
  });
}

export function useNewsImpact(symbol: string | undefined) {
  return useQuery({
    queryKey: ["news-impact", symbol],
    queryFn: () => newsRepository.impact(symbol as string),
    enabled: Boolean(symbol),
    retry: false,
  });
}
