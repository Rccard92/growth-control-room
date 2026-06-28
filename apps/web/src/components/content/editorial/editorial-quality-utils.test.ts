import { describe, expect, it } from "vitest";
import type { EditorialArticlePayload } from "@gcr/shared";
import { analyzeEditorialQuality } from "./editorial-quality-utils";

const sampleArticle: EditorialArticlePayload = {
  title: "Guida miele",
  handle: "guida-miele",
  excerpt: "Intro",
  bodyHtml: `
    <div class="gcr-article-body">
    <h2>Qualità</h2>
    <p><strong>La cristallizzazione è naturale</strong>.</p>
    <ul><li>Colore</li><li>Profumo</li></ul>
    <div class="gcr-article-note"><strong>Da ricordare:</strong> test</div>
    </div>
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
  skillPackVersion: "v1.1",
  safeClaimFlags: [
    {
      severity: "medium",
      phrase: "Il miele aiuta il benessere quotidiano.",
      reason: "Possibile claim salutistico",
      suggestion: "Sostituire con formulazione descrittiva non terapeutica",
    },
  ],
};

describe("editorial-quality-utils", () => {
  it("analizza grassetti, liste, box e wrapper body", () => {
    const q = analyzeEditorialQuality(sampleArticle);
    expect(q.skillPackUsed).toBe("gcr-editorial-article");
    expect(q.skillPackVersion).toBe("v1.1");
    expect(q.strongCount).toBeGreaterThanOrEqual(2);
    expect(q.strongInRange).toBe(false);
    expect(q.listCount).toBe(1);
    expect(q.boxCount).toBe(1);
    expect(q.hasCta).toBe(true);
    expect(q.hasBodyWrapper).toBe(true);
    expect(q.hasLongParagraphs).toBe(false);
  });

  it("espone safeClaimFlags con frase precisa", () => {
    const q = analyzeEditorialQuality(sampleArticle);
    expect(q.safeClaimFlags).toHaveLength(1);
    expect(q.safeClaimFlags[0].phrase).toContain("benessere");
    expect(q.safeClaimFlags[0].severity).toBe("medium");
  });
});
