import type { NotificationPriority, Rating, RiskLevel } from "./enums";

export interface NotificationFeedItem {
  symbol?: string | null;
  rating?: Rating | null;
  category: string;
  sent_at: string;
  status: string;
}

export interface NotificationFeedResponse {
  items: NotificationFeedItem[];
}

export interface RunResult {
  evaluated: number;
  sent: number;
  skipped_quiet_hours: boolean;
}

export interface NotificationPreference {
  categories: string[];
  min_priority: NotificationPriority;
  max_risk: RiskLevel;
  sectors: string[];
  quiet_hours_start?: number | null;
  quiet_hours_end?: number | null;
}
