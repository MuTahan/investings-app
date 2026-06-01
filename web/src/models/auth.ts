import type { RiskTolerance, TimeHorizon } from "./enums";

export interface UserPublic {
  id: string;
  email?: string | null;
  display_name?: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserPublic;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface RiskProfile {
  risk_tolerance: RiskTolerance;
  time_horizon: TimeHorizon;
  objectives: string[];
  max_position_pct?: number | null;
}

export interface Me {
  id: string;
  email?: string | null;
  display_name?: string | null;
  risk_profile?: RiskProfile | null;
}

export interface RegisterPayload {
  email: string;
  password: string;
  display_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}
