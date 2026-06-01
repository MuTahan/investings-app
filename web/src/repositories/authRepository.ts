import { apiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type {
  LoginPayload,
  Me,
  RegisterPayload,
  RiskProfile,
  TokenResponse,
} from "../models/auth";

export const authRepository = {
  register: (payload: RegisterPayload) =>
    apiClient.post<TokenResponse>(endpoints.auth.register, payload, { auth: false }),

  login: (payload: LoginPayload) =>
    apiClient.post<TokenResponse>(endpoints.auth.login, payload, { auth: false }),

  apple: (identityToken: string, nonce?: string, fullName?: string) =>
    apiClient.post<TokenResponse>(
      endpoints.auth.apple,
      { identity_token: identityToken, nonce, full_name: fullName },
      { auth: false },
    ),

  me: () => apiClient.get<Me>(endpoints.me),

  updateRiskProfile: (profile: RiskProfile) =>
    apiClient.put<RiskProfile>(endpoints.riskProfile, profile),
};
