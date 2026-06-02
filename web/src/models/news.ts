import type { NewsCategory, Rating } from "./enums";

export interface NewsItem {
  headline: string;
  summary?: string | null;
  url: string;
  source?: string | null;
  published_at?: string | null;
  sentiment?: number | null;
  category: NewsCategory;
}

export interface NewsImpactItem {
  headline: string;
  url: string;
  source?: string | null;
  published_at?: string | null;
  impact_score: number;
  impact_label: string;
}

export interface NewsImpactReport {
  symbol: string;
  article_count: number;
  net_sentiment: number;
  sentiment_label: string;
  predicted_short_term: string;
  predicted_long_term: string;
  recommended_action?: Rating | null;
  confidence?: number | null;
  summary: string;
  items: NewsImpactItem[];
}
