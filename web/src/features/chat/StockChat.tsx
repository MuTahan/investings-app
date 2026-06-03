import { type FormEvent, useEffect, useRef, useState } from "react";

import { isApiError } from "../../api/errors";
import { Button } from "../../components/ui/Button";
import { ErrorPanel } from "../../components/ui/StatePanel";
import { useSendChat } from "../../hooks/useChat";
import { cn } from "../../lib/cn";
import type { ChatMessage } from "../../models/chat";

export function StockChat({
  symbol,
  suggestions,
  heightClass = "h-[420px]",
}: {
  symbol?: string;
  suggestions?: string[];
  heightClass?: string;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const send = useSendChat();
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, send.isPending]);

  const submit = (text: string) => {
    const content = text.trim();
    if (!content || send.isPending) return;
    const next: ChatMessage[] = [...messages, { role: "user", content }];
    setMessages(next);
    setDraft("");
    send.mutate(
      { symbol, messages: next },
      {
        onSuccess: (res) =>
          setMessages((m) => [...m, { role: "assistant", content: res.reply }]),
      },
    );
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    submit(draft);
  };

  return (
    <div className="flex flex-col">
      <div className={cn("space-y-3 overflow-y-auto pr-1", heightClass)}>
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
            <p className="text-sm text-muted">
              {symbol
                ? `Ask anything about ${symbol.toUpperCase()} — grounded in its live price, AI rating & news.`
                : "Ask about any US stock or ETF. Mention a ticker for grounded answers."}
            </p>
            {suggestions && suggestions.length > 0 && (
              <div className="flex flex-wrap justify-center gap-2">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => submit(s)}
                    className="rounded-full border border-border bg-surface-2 px-3 py-1.5 text-xs font-medium text-fg-soft transition-colors hover:border-primary hover:text-primary"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}>
            <div
              className={cn(
                "max-w-[85%] whitespace-pre-wrap rounded-2xl px-3.5 py-2 text-sm",
                m.role === "user"
                  ? "bg-primary text-primary-fg"
                  : "bg-surface-2 text-fg ring-1 ring-inset ring-border",
              )}
            >
              {m.content}
            </div>
          </div>
        ))}

        {send.isPending && (
          <div className="flex justify-start">
            <div className="flex gap-1 rounded-2xl bg-surface-2 px-3.5 py-3 ring-1 ring-inset ring-border">
              {[0, 150, 300].map((d) => (
                <span
                  key={d}
                  className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted"
                  style={{ animationDelay: `${d}ms` }}
                />
              ))}
            </div>
          </div>
        )}
        {send.isError && (
          <ErrorPanel message={isApiError(send.error) ? send.error.message : "Chat failed."} />
        )}
        <div ref={endRef} />
      </div>

      <form onSubmit={onSubmit} className="mt-3 flex items-end gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={symbol ? `Message about ${symbol.toUpperCase()}…` : "Type a message…"}
          className="flex-1 rounded-lg border border-border bg-surface-2 px-3 py-2.5 text-sm text-fg outline-none transition-colors placeholder:text-faint focus:border-primary focus:ring-2 focus:ring-primary/30"
        />
        <Button type="submit" loading={send.isPending} disabled={!draft.trim()}>
          Send
        </Button>
      </form>
    </div>
  );
}
