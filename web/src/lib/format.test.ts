import { describe, expect, it } from "vitest";

import { changeColor, formatCurrency, formatPercent } from "./format";

describe("format", () => {
  it("formats currency and handles null", () => {
    expect(formatCurrency(1234.5)).toBe("$1,234.50");
    expect(formatCurrency(null)).toBe("—");
  });

  it("formats signed percent", () => {
    expect(formatPercent(1.5)).toBe("+1.50%");
    expect(formatPercent(-2)).toBe("-2.00%");
    expect(formatPercent(null)).toBe("—");
  });

  it("picks change color by sign", () => {
    expect(changeColor(1)).toBe("text-bull");
    expect(changeColor(-1)).toBe("text-bear");
    expect(changeColor(0)).toBe("text-muted");
  });
});
