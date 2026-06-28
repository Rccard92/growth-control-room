import { describe, expect, it } from "vitest";
import type { ContentSeoEditorialItem } from "@gcr/shared";
import { getEditorialDisplayTitle } from "./editorial-display-utils";

function baseItem(overrides: Partial<ContentSeoEditorialItem> = {}): ContentSeoEditorialItem {
  return {
    id: "item-1",
    projectId: "proj-1",
    title: "Guida: argomento SEO",
    contentType: "educational_article",
    plannedDate: "2026-06-15",
    status: "idea",
    createdAt: "2026-06-01T00:00:00Z",
    updatedAt: "2026-06-01T00:00:00Z",
    ...overrides,
  };
}

describe("getEditorialDisplayTitle", () => {
  it("prefers article title", () => {
    const item = baseItem({
      articlePayload: {
        title: "Perché il miele cristallizza?",
        handle: "miele",
        excerpt: "",
        bodyHtml: "",
        bodyMarkdown: "",
        seoTitle: "",
        metaDescription: "",
        tags: [],
        linkedProducts: [],
        cta: "",
        status: "draft",
        warnings: [],
        brandContextUsed: [],
        generatedAt: "",
      },
      briefPayload: { proposedTitle: "Brief title" },
    });
    expect(getEditorialDisplayTitle(item)).toBe("Perché il miele cristallizza?");
  });

  it("falls back to brief proposedTitle", () => {
    const item = baseItem({
      briefPayload: { proposedTitle: "Perché il miele cristallizza? Guida semplice" },
    });
    expect(getEditorialDisplayTitle(item)).toBe("Perché il miele cristallizza? Guida semplice");
  });

  it("falls back to item.title", () => {
    expect(getEditorialDisplayTitle(baseItem())).toBe("Guida: argomento SEO");
  });

  it("uses final fallback when empty", () => {
    expect(getEditorialDisplayTitle(baseItem({ title: "  " }))).toBe("Contenuto editoriale");
  });
});
