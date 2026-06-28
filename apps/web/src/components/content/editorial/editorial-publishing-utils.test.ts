import { describe, expect, it } from "vitest";
import type { EditorialArticlePayload } from "@gcr/shared";
import {
  buildPublishingPayloadFromArticle,
  parseEditorialPublishingPayload,
  validatePublishingPayload,
} from "./editorial-publishing-utils";

const sampleArticle: EditorialArticlePayload = {
  title: "Guida olio EVO",
  handle: "guida-olio-evo",
  excerpt: "Tutto sull'olio.",
  bodyHtml: "<h2>Intro</h2><p>Testo.</p>",
  bodyMarkdown: "",
  seoTitle: "Olio EVO guida",
  metaDescription: "Meta desc",
  tags: ["olio"],
  linkedProducts: [],
  cta: "",
  authorName: "Davide",
  status: "draft",
  warnings: [],
  brandContextUsed: [],
  generatedAt: "",
};

describe("editorial-publishing-utils", () => {
  it("precompila da articlePayload", () => {
    const payload = buildPublishingPayloadFromArticle(sampleArticle);
    expect(payload.title).toBe("Guida olio EVO");
    expect(payload.bodyHtml).toContain("<h2>");
    expect(payload.author).toBe("Davide");
    expect(payload.mode).toBe("draft");
  });

  it("valida campi obbligatori", () => {
    const payload = parseEditorialPublishingPayload({ title: "", bodyHtml: "" });
    const errors = validatePublishingPayload(payload);
    expect(errors.length).toBeGreaterThanOrEqual(2);
  });

  it("richiede blog per publish", () => {
    const payload = buildPublishingPayloadFromArticle(sampleArticle);
    const errors = validatePublishingPayload(payload, { forPublish: true });
    expect(errors.some((e) => e.toLowerCase().includes("blog"))).toBe(true);
  });
});
