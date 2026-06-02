import { apiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type { NewsImpactReport, NewsItem } from "../models/news";

interface NewsListResponse {
  items: NewsItem[];
}

export const newsRepository = {
  list: (symbol: string | null, category = "company", limit = 20) =>
    apiClient.get<NewsListResponse>(endpoints.news(symbol, category, limit)),

  impact: (symbol: string) => apiClient.get<NewsImpactReport>(endpoints.newsImpact(symbol)),
};
