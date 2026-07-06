import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { DataForSeoTestResponse } from "@gcr/shared";
import { DataForSeoTestResultPanel } from "./DataForSeoTestResultPanel";

const searchVolumeResult: DataForSeoTestResponse = {
  testType: "search_volume_batch",
  keyword: "polline biologico",
  keywords: ["polline biologico", "miele di eucalipto"],
  costUsd: 0.18,
  averageCostPerKeywordUsd: 0.09,
  endpoints: ["/keywords_data/google_ads/search_volume/live"],
  responseSummary: {
    keywordCount: 2,
    results: [
      {
        keyword: "polline biologico",
        searchVolume: 1200,
        cpc: 0.42,
        competition: "MEDIUM",
        competitionIndex: 55,
        trend: { direction: "up", lastMonth: 1300, averageLast12Months: 1100 },
      },
      {
        keyword: "miele di eucalipto",
        searchVolume: 800,
        cpc: 0.35,
        competition: "LOW",
        competitionIndex: 20,
        trend: { direction: "stable", lastMonth: 800, averageLast12Months: 790 },
      },
    ],
  },
  rawPreview: { truncated: true },
};

describe("DataForSeoTestResultPanel", () => {
  it("renders readable table without raw JSON in main view", () => {
    const html = renderToStaticMarkup(<DataForSeoTestResultPanel result={searchVolumeResult} />);
    expect(html).toContain("polline biologico");
    expect(html).toContain("Volume");
    expect(html).toContain("In crescita");
    expect(html).not.toContain('"truncated": true');
  });

  it("keeps raw response inside details", () => {
    const html = renderToStaticMarkup(<DataForSeoTestResultPanel result={searchVolumeResult} />);
    expect(html).toContain("<details");
    expect(html).toContain("Raw response tecnica");
  });
});
