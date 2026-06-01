import type { Rating } from "./enums";

export interface NotificationFeedItem {
  symbol?: string | null;
  rating?: Rating | null;
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
