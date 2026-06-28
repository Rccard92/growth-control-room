import { describe, expect, it } from "vitest";
import type { EditorialArticlePayload, EditorialPublishingPayload } from "@gcr/shared";
import {
  buildArticleHashCanonical,
  isPublishingStale,
  isPublishingSyncUnknown,
} from "./editorial-publishing-utils";

const sampleArticle: EditorialArticlePayload = {
  title: "Guida miele",
  handle: "guida-miele",
  excerpt: "Intro",
  bodyHtml: "<p>Test</p>",
  bodyMarkdown: "",
  seoTitle: "",
  metaDescription: "",
  tags: [],
  linkedProducts: [],
  cta: "Scopri",
  status: "draft",
  warnings: [],
  brandContextUsed: [],
  generatedAt: "",
  articleHash: "abc123",
  skillPackUsed: "gcr-editorial-article",
  skillPackVersion: "v1.1",
};

const samplePublishing: EditorialPublishingPayload = {
  title: "Guida miele",
  handle: "guida-miele",
  bodyHtml: "<p>Old</p>",
  excerpt: "",
  seoTitle: "",
  metaDescription: "",
  author: "Redazione",
  tags: [],
  mode: "draft",
  isPublished: false,
  sourceArticleHash: "old-hash",
};

describe("editorial-publishing-utils sync", () => {
  it("rileva publishing stale quando hash differisce", () => {
    expect(isPublishingStale(sampleArticle, samplePublishing)).toBe(true);
  });

  it("non segnala stale se hash allineati", () => {
    const publishing = { ...samplePublishing, sourceArticleHash: "abc123" };
    expect(isPublishingStale(sampleArticle, publishing)).toBe(false);
  });

  it("buildArticleHashCanonical ordina i tag", () => {
    const canonical = buildArticleHashCanonical({
      ...sampleArticle,
      title: " Titolo ",
      tags: ["b", "a"],
    });
    expect(canonical).toContain('"title":"Titolo"');
    expect(canonical).toContain('"tags":"a,b"');
  });

  it("isPublishingSyncUnknown se manca sourceArticleHash", () => {
    expect(
      isPublishingSyncUnknown(sampleArticle, { ...samplePublishing, sourceArticleHash: null }, true),
    ).toBe(true);
  });
});
