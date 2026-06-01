import type { NewsCategory } from "./enums";

export interface NewsItem {
  headline: string;
  summary?: string | null;
  url: string;
  source?: string | null;
  published_at?: string | null;
  sentiment?: number | null;
  category: NewsCategory;
}
