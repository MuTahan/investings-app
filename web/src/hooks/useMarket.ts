import { useQuery } from "@tanstack/react-query";

import { marketRepository } from "../repositories/marketRepository";

export function useSearch(query: string) {
  const trimmed = query.trim();
  return useQuery({
    queryKey: ["search", trimmed],
    queryFn: () => marketRepository.search(trimmed),
    enabled: trimmed.length >= 1,
  });
}

export function useInstrument(symbol: string | undefined) {
  return useQuery({
    queryKey: ["instrument", symbol],
    queryFn: () => marketRepository.instrument(symbol as string),
    enabled: Boolean(symbol),
  });
}

export function useQuote(symbol: string | undefined) {
  return useQuery({
    queryKey: ["quote", symbol],
    queryFn: () => marketRepository.quote(symbol as string),
    enabled: Boolean(symbol),
    refetchInterval: 30_000,
  });
}

export function useCandles(symbol: string | undefined, resolution = "D", days = 180) {
  return useQuery({
    queryKey: ["candles", symbol, resolution, days],
    queryFn: () => marketRepository.candles(symbol as string, resolution, days),
    enabled: Boolean(symbol),
  });
}

export function useTrending(category: string) {
  return useQuery({
    queryKey: ["trending", category],
    queryFn: () => marketRepository.trending(category),
    staleTime: 60_000,
  });
}
