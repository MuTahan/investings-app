import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  portfolioRepository,
  type AddHoldingPayload,
  type UpdateHoldingPayload,
} from "../repositories/portfolioRepository";

const KEY = ["portfolio"];

export function usePortfolio() {
  return useQuery({ queryKey: KEY, queryFn: () => portfolioRepository.get() });
}

export function useAddHolding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AddHoldingPayload) => portfolioRepository.addHolding(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: KEY }),
  });
}

export function useUpdateHolding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateHoldingPayload }) =>
      portfolioRepository.updateHolding(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: KEY }),
  });
}

export function useDeleteHolding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => portfolioRepository.deleteHolding(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: KEY }),
  });
}
