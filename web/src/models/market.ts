import type { InstrumentType } from "./enums";

export interface Instrument {
  id: string;
  symbol: string;
  name: string;
  type: InstrumentType;
  exchange?: string | null;
  sector?: string | null;
  currency: string;
}

export interface Quote {
  symbol: string;
  price: number;
  change?: number | null;
  change_pct?: number | null;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  prev_close?: number | null;
  volume?: number | null;
  as_of?: string | null;
}

export interface Candle {
  t: string;
  o: number;
  h: number;
  l: number;
  c: number;
  v?: number | null;
}

export interface CandleSeries {
  symbol: string;
  resolution: string;
  candles: Candle[];
}

export interface SearchResponse {
  results: Instrument[];
}
