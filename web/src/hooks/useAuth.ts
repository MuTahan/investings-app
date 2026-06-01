import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import type { LoginPayload, RegisterPayload, RiskProfile, TokenResponse } from "../models/auth";
import { authRepository } from "../repositories/authRepository";
import { useAuthStore } from "../store/authStore";

function applySession(res: TokenResponse) {
  useAuthStore.getState().setSession(res.user, res.access_token, res.refresh_token);
}

export function useLogin() {
  return useMutation({
    mutationFn: (payload: LoginPayload) => authRepository.login(payload),
    onSuccess: applySession,
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: (payload: RegisterPayload) => authRepository.register(payload),
    onSuccess: applySession,
  });
}

export function useMe(enabled = true) {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => authRepository.me(),
    enabled,
  });
}

export function useUpdateRiskProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (profile: RiskProfile) => authRepository.updateRiskProfile(profile),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}
