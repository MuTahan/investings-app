import { useMutation } from "@tanstack/react-query";

import type { ChatMessage } from "../models/chat";
import { chatRepository } from "../repositories/chatRepository";

export function useSendChat() {
  return useMutation({
    mutationFn: (vars: { symbol?: string | null; messages: ChatMessage[] }) =>
      chatRepository.send(vars),
  });
}
