import { describe, expect, it } from "vitest";
import type { EditorialArticlePayload, EditorialPublishingPayload } from "@gcr/shared";
import {
  buildArticleHashCanonical,
  getPublishingSeoWarnings,
  isPublishingStale,
  validatePublishingPayload,
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

  it("rileva publishing stale se manca sourceArticleHash", () => {
    expect(
      isPublishingStale(sampleArticle, { ...samplePublishing, sourceArticleHash: null }),
    ).toBe(true);
  });

  it("non segnala stale senza publishing", () => {
    expect(isPublishingStale(sampleArticle, null)).toBe(false);
  });

  it("richiede SEO title e meta description per publish", () => {
    const payload = {
      ...samplePublishing,
      title: "Guida miele",
      bodyHtml: "<p>Test</p>",
      author: "Redazione",
      blogId: "blog-1",
      handle: "guida-miele",
      seoTitle: "",
      metaDescription: "",
    };
    const errors = validatePublishingPayload(payload, { forPublish: true });
    expect(errors.some((e) => e.includes("SEO title e meta description"))).toBe(true);
  });

  it("avvisa se SEO title oltre soglia", () => {
    const warnings = getPublishingSeoWarnings({
      ...samplePublishing,
      seoTitle: "x".repeat(61),
      metaDescription: "ok",
    });
    expect(warnings.length).toBeGreaterThan(0);
  });
});
