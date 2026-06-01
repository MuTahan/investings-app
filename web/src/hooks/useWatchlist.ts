import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { watchlistRepository } from "../repositories/watchlistRepository";

const KEY = ["watchlist"];

export function useWatchlist() {
  return useQuery({ queryKey: KEY, queryFn: () => watchlistRepository.get() });
}

export function useAddWatchlistItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (symbol: string) => watchlistRepository.addItem(symbol),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: KEY }),
  });
}

export function useRemoveWatchlistItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (instrumentId: string) => watchlistRepository.removeItem(instrumentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: KEY }),
  });
}
