import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { RatingBadge } from "../components/ui/Badge";
import { InstrumentRow } from "../features/markets/InstrumentRow";

function withProviders(ui: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("RatingBadge", () => {
  it("renders the rating label", () => {
    render(<RatingBadge rating="STRONG_BUY" />);
    expect(screen.getByText("STRONG BUY")).toBeInTheDocument();
  });
});

describe("InstrumentRow", () => {
  it("renders symbol, name, and links to the detail page", () => {
    render(
      withProviders(
        <InstrumentRow
          instrument={{
            id: "1",
            symbol: "AAPL",
            name: "Apple Inc.",
            type: "stock",
            currency: "USD",
          }}
        />,
      ),
    );
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("Apple Inc.")).toBeInTheDocument();
    expect(screen.getByRole("link")).toHaveAttribute("href", "/markets/AAPL");
  });
});
