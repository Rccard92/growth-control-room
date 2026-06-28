import { describe, expect, it } from "vitest";
import type { EditorialArticlePayload } from "@gcr/shared";
import { analyzeEditorialQuality } from "./editorial-quality-utils";

const sampleArticle: EditorialArticlePayload = {
  title: "Guida miele",
  handle: "guida-miele",
  excerpt: "Intro",
  bodyHtml: `
    <h2>Qualità</h2>
    <p><strong>La cristallizzazione è naturale</strong>.</p>
    <ul><li>Colore</li><li>Profumo</li></ul>
    <div class="gcr-article-note"><strong>Da ricordare:</strong> test</div>
  `,
  bodyMarkdown: "",
  seoTitle: "",
  metaDescription: "",
  tags: [],
  linkedProducts: [],
  cta: "Scopri la selezione",
  status: "draft",
  warnings: [],
  brandContextUsed: [],
  generatedAt: "",
  skillPackUsed: "gcr-editorial-article",
  skillPackVersion: "v1",
};

describe("editorial-quality-utils", () => {
  it("analizza grassetti, liste e box", () => {
    const q = analyzeEditorialQuality(sampleArticle);
    expect(q.skillPackUsed).toBe("gcr-editorial-article");
    expect(q.strongCount).toBeGreaterThanOrEqual(2);
    expect(q.listCount).toBe(1);
    expect(q.boxCount).toBe(1);
    expect(q.hasCta).toBe(true);
    expect(q.hasLongParagraphs).toBe(false);
  });
});
