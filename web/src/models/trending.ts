import type { InstrumentType, Signal } from "./enums";

export interface TrendingItem {
  id: string;
  symbol: string;
  name: string;
  type: InstrumentType;
  price?: number | null;
  change_pct?: number | null;
  sentiment: Signal;
  trend_score: number;
  summary: string;
}

export interface TrendingResponse {
  category: string;
  items: TrendingItem[];
}

export const TRENDING_CATEGORIES = [
  { key: "trending", label: "Trending now" },
  { key: "most_bought", label: "Most bought" },
  { key: "most_sold", label: "Most sold" },
  { key: "high_momentum", label: "High momentum" },
  { key: "high_opportunity", label: "High opportunity" },
] as const;
