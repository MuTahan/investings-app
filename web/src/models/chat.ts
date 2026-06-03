export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  symbol?: string | null;
  messages: ChatMessage[];
}

export interface ChatResponse {
  reply: string;
}
