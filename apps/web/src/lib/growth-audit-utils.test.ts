import { describe, expect, it } from "vitest";
import {
  getDefaultRootUrl,
  getGrowthAuditPageTypeLabel,
  getGrowthAuditPhaseLabel,
  getGrowthAuditStatusLabel,
} from "./growth-audit-utils";

describe("growth-audit-utils", () => {
  it("translates run status to Italian", () => {
    expect(getGrowthAuditStatusLabel("completed")).toBe("Completato");
    expect(getGrowthAuditStatusLabel("discovering")).toBe("Discovery in corso");
  });

  it("translates phase to Italian", () => {
    expect(getGrowthAuditPhaseLabel("classification")).toBe("Classificazione");
    expect(getGrowthAuditPhaseLabel("ready_for_analysis")).toBe("Pronto per analisi");
  });

  it("translates page type to Italian", () => {
    expect(getGrowthAuditPageTypeLabel("homepage")).toBe("Homepage");
    expect(getGrowthAuditPageTypeLabel("product")).toBe("Prodotto");
  });

  it("builds default root URL from shop domain", () => {
    expect(getDefaultRootUrl("shop.example.com")).toBe("https://shop.example.com");
    expect(getDefaultRootUrl("https://shop.example.com")).toBe("https://shop.example.com");
  });
});
