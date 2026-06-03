import { Card, CardHeader } from "../../components/ui/Card";
import { StockChat } from "./StockChat";

const SUGGESTIONS = [
  "Explain what a P/E ratio tells me",
  "What's the difference between an ETF and a stock?",
  "How should I think about diversification?",
  "What does the AI rating mean here?",
];

export function ChatPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Assistant</h1>
        <p className="text-sm text-muted">Chat about US stocks &amp; ETFs · powered by Grok</p>
      </header>
      <Card>
        <CardHeader title="Chat" />
        <StockChat suggestions={SUGGESTIONS} heightClass="h-[60vh]" />
        <p className="mt-2 text-xs text-faint">
          Informational only — not financial advice. Mention a ticker (e.g. AAPL) for live context.
        </p>
      </Card>
    </div>
  );
}
