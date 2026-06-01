import type {
  NotificationPriority,
  Rating,
  RiskLevel,
  Signal,
  TimeHorizon,
} from "./enums";

export interface Reason {
  label: string;
  detail: string;
}

export interface RiskNote {
  label: string;
  detail: string;
  severity: string;
}

export interface Personalization {
  fit_score?: number | null;
  fit_reason?: string | null;
}

export interface AgentBreakdown {
  agent: string;
  base_score?: number | null;
  score?: number | null;
  adjustment_delta: number;
  confidence: number;
  signal?: Signal | null;
  explanation?: string | null;
  adjustment_justification?: string | null;
  risk_level?: RiskLevel | null;
  warnings: string[];
}

export interface RecommendationDetail {
  symbol: string;
  rating: Rating;
  anchor_rating: Rating;
  confidence: number;
  composite_score: number;
  decision_mode: string;
  time_horizon: TimeHorizon;
  suggested_action?: string | null;
  chair_rationale?: string | null;
  reasons: Reason[];
  risks: RiskNote[];
  personalization?: Personalization | null;
  agent_breakdown: AgentBreakdown[];
  notif_priority: NotificationPriority;
  weights_version: string;
  model_versions: Record<string, string>;
  generated_at: string;
}
