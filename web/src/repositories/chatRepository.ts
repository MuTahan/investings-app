import { apiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type { ChatRequest, ChatResponse } from "../models/chat";

export const chatRepository = {
  send: (req: ChatRequest) => apiClient.post<ChatResponse>(endpoints.chat, req),
};
