import { apiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type { CandleSeries, Instrument, Quote, SearchResponse } from "../models/market";
import type { TrendingResponse } from "../models/trending";

export const marketRepository = {
  search: (q: string, limit = 20) =>
    apiClient.get<SearchResponse>(endpoints.market.search(q, limit)),

  instrument: (symbol: string) =>
    apiClient.get<Instrument>(endpoints.market.instrument(symbol)),

  quote: (symbol: string) => apiClient.get<Quote>(endpoints.market.quote(symbol)),

  candles: (symbol: string, resolution = "D", days = 180) =>
    apiClient.get<CandleSeries>(endpoints.market.candles(symbol, resolution, days)),

  trending: (category = "trending", limit = 12) =>
    apiClient.get<TrendingResponse>(endpoints.market.trending(category, limit)),
};
