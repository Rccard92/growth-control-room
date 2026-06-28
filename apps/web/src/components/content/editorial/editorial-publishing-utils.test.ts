import { describe, expect, it } from "vitest";
import type { EditorialArticlePayload, EditorialPublishingPayload } from "@gcr/shared";
import {
  buildArticleHashCanonical,
  formatPedScheduleMessage,
  formatPublishingError,
  formatScheduledPublishLabel,
  getPrimaryPublishAction,
  getPublishingSeoWarnings,
  isPublishingStale,
  parseStructuredPublishErrorDetail,
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

  it("estrae message da errore strutturato publish", () => {
    const parsed = parseStructuredPublishErrorDetail({
      message: "SEO mancante",
      code: "seo_missing",
      details: {},
    });
    expect(parsed?.message).toBe("SEO mancante");
    expect(parsed?.code).toBe("seo_missing");
  });

  it("aggiunge hint per errore Field seo GraphQL", () => {
    const message = formatPublishingError(
      "Errore invio articolo Shopify.",
      new Error("Field `seo` doesn't exist on type `Article`"),
    );
    expect(message).toContain("campo GraphQL non supportato");
  });

  it("aggiunge hint per errore isPublished con data futura", () => {
    const message = formatPublishingError(
      "Errore invio articolo Shopify.",
      new Error("Can't set isPublished to true and also set a future publish date."),
    );
    expect(message).toContain("modalità Programmato");
  });

  it("data futura mostra azione Programma su Shopify", () => {
    const action = getPrimaryPublishAction({
      plannedDate: "2099-07-05",
      timezone: "Europe/Rome",
      publishingStale: false,
      hasShopifyLink: false,
      isPublishedOnShopify: false,
    });
    expect(action.mode).toBe("schedule");
    expect(action.label).toContain("Programma su Shopify");
  });

  it("data passata mostra warning nel messaggio PED", () => {
    const message = formatPedScheduleMessage("2020-01-01", "09:00", "Europe/Rome");
    expect(message).toContain("passata");
  });

  it("formatta badge programmato", () => {
    const label = formatScheduledPublishLabel("2026-07-05T09:00:00+02:00", "Europe/Rome");
    expect(label).toContain("Programmato");
  });
});
