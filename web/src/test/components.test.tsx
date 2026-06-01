import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { RatingBadge } from "../components/ui/Badge";
import { InstrumentRow } from "../features/markets/InstrumentRow";

describe("RatingBadge", () => {
  it("renders the rating label", () => {
    render(<RatingBadge rating="STRONG_BUY" />);
    expect(screen.getByText("STRONG BUY")).toBeInTheDocument();
  });
});

describe("InstrumentRow", () => {
  it("renders symbol, name, and links to the detail page", () => {
    render(
      <MemoryRouter>
        <InstrumentRow
          instrument={{
            id: "1",
            symbol: "AAPL",
            name: "Apple Inc.",
            type: "stock",
            currency: "USD",
          }}
        />
      </MemoryRouter>,
    );
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("Apple Inc.")).toBeInTheDocument();
    expect(screen.getByRole("link")).toHaveAttribute("href", "/markets/AAPL");
  });
});
