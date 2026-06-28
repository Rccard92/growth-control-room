import type { EditorialArticlePayload } from "@gcr/shared";

export function emptyEditorialArticlePayload(): EditorialArticlePayload {
  return {
    title: "",
    handle: "",
    excerpt: "",
    bodyHtml: "",
    bodyMarkdown: "",
    seoTitle: "",
    metaDescription: "",
    tags: [],
    linkedProducts: [],
    cta: "",
    authorName: "",
    authorRole: "",
    communityCta: "",
    estimatedReadingTime: "",
    contentLengthProfile: undefined,
    status: "draft",
    warnings: [],
    brandContextUsed: [],
    generatedAt: "",
    readabilityChecklist: [],
    neuromarketingElements: [],
    internalLinkSuggestions: [],
    htmlBlocksUsed: [],
    skillPackUsed: "",
    skillPackVersion: "",
  };
}

function coerceStringList(value: unknown): string[] {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.map((v) => String(v).trim()).filter(Boolean);
  }
  if (typeof value === "string") {
    return value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
  }
  return [];
}

export function parseEditorialArticlePayload(
  raw: Record<string, unknown> | null | undefined,
): EditorialArticlePayload {
  if (!raw || Object.keys(raw).length === 0) {
    return emptyEditorialArticlePayload();
  }
  return {
    title: String(raw.title ?? ""),
    handle: String(raw.handle ?? ""),
    excerpt: String(raw.excerpt ?? ""),
    bodyHtml: String(raw.bodyHtml ?? ""),
    bodyMarkdown: String(raw.bodyMarkdown ?? ""),
    seoTitle: String(raw.seoTitle ?? ""),
    metaDescription: String(raw.metaDescription ?? ""),
    tags: coerceStringList(raw.tags),
    linkedProducts: coerceStringList(raw.linkedProducts),
    cta: String(raw.cta ?? ""),
    authorName: String(raw.authorName ?? ""),
    authorRole: String(raw.authorRole ?? ""),
    communityCta: String(raw.communityCta ?? ""),
    estimatedReadingTime: String(raw.estimatedReadingTime ?? ""),
    contentLengthProfile:
      raw.contentLengthProfile === "breve" ||
      raw.contentLengthProfile === "medio" ||
      raw.contentLengthProfile === "approfondito"
        ? raw.contentLengthProfile
        : undefined,
    status: "draft",
    warnings: coerceStringList(raw.warnings),
    brandContextUsed: coerceStringList(raw.brandContextUsed),
    generatedAt: String(raw.generatedAt ?? ""),
    readabilityChecklist: coerceStringList(raw.readabilityChecklist),
    neuromarketingElements: coerceStringList(raw.neuromarketingElements),
    internalLinkSuggestions: coerceStringList(raw.internalLinkSuggestions),
    htmlBlocksUsed: coerceStringList(raw.htmlBlocksUsed),
    skillPackUsed: String(raw.skillPackUsed ?? ""),
    skillPackVersion: String(raw.skillPackVersion ?? ""),
  };
}

export function hasEditorialArticle(
  raw: Record<string, unknown> | EditorialArticlePayload | null | undefined,
): boolean {
  if (!raw || Object.keys(raw).length === 0) return false;
  const parsed =
    "bodyHtml" in raw && typeof raw.bodyHtml === "string"
      ? (raw as EditorialArticlePayload)
      : parseEditorialArticlePayload(raw as Record<string, unknown>);
  return Boolean(
    parsed.title.trim() ||
      parsed.bodyHtml.trim() ||
      parsed.bodyMarkdown.trim() ||
      parsed.excerpt.trim(),
  );
}

export function listToTextarea(lines: string[]): string {
  return lines.join("\n");
}

export function textareaToList(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}
