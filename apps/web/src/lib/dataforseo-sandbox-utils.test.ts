import { describe, expect, it } from "vitest";
import {
  formatCostPerItem,
  formatTrend,
  parseKeywordBatch,
  SEARCH_VOLUME_BATCH_MAX_KEYWORDS,
  SOLMIELATO_DEFAULT_KEYWORDS,
} from "./dataforseo-sandbox-utils";

describe("dataforseo-sandbox-utils", () => {
  it("parses batch keywords from lines and commas with dedup", () => {
    const parsed = parseKeywordBatch("a\nb, a\nc");
    expect(parsed).toEqual(["a", "b", "c"]);
  });

  it("exposes max 10 keywords constant", () => {
    expect(SEARCH_VOLUME_BATCH_MAX_KEYWORDS).toBe(10);
    expect(SOLMIELATO_DEFAULT_KEYWORDS).toHaveLength(10);
  });

  it("formats trend labels", () => {
    expect(formatTrend("up")).toContain("crescita");
    expect(formatTrend("stable")).toContain("Stabile");
  });

  it("formats cost per item", () => {
    expect(formatCostPerItem(0.45, 5)).toBe("$0.0900");
    expect(formatCostPerItem(null, 5)).toBe("—");
  });
});
