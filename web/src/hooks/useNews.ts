import { useQuery } from "@tanstack/react-query";

import { newsRepository } from "../repositories/newsRepository";

export function useNews(symbol: string | null, category = "company") {
  return useQuery({
    queryKey: ["news", symbol, category],
    queryFn: () => newsRepository.list(symbol, category),
  });
}
