import type { Instrument, Quote } from "./market";

export interface Holding {
  id: string;
  instrument: Instrument;
  quantity: number;
  avg_cost: number;
  market_value?: number | null;
  unrealized_pl?: number | null;
  unrealized_pl_pct?: number | null;
  weight?: number | null;
}

export interface PortfolioSummary {
  market_value: number;
  cost_basis: number;
  unrealized_pl: number;
  unrealized_pl_pct: number;
  diversification_score: number;
  sector_exposure: Record<string, number>;
}

export interface Portfolio {
  id: string;
  name: string;
  summary: PortfolioSummary;
  holdings: Holding[];
}

export interface WatchlistItem {
  instrument: Instrument;
  quote?: Quote | null;
  added_at?: string | null;
}

export interface Watchlist {
  id: string;
  name: string;
  items: WatchlistItem[];
}
