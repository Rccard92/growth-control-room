import type { EditorialBriefPayload } from "@gcr/shared";

export function emptyEditorialBriefPayload(): EditorialBriefPayload {
  return {
    proposedTitle: "",
    searchIntent: "",
    targetAudience: "",
    primaryKeyword: "",
    secondaryKeywords: [],
    contentAngle: "",
    h2H3Structure: [],
    productsToLink: [],
    faqToInclude: [],
    claimsToAvoid: [],
    safeClaimsToUse: [],
    recommendedCta: "",
    metaTitle: "",
    metaDescription: "",
    internalLinksSuggestions: [],
    notes: "",
    brandContextUsed: [],
    warnings: [],
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

export function parseEditorialBriefPayload(
  raw: Record<string, unknown> | null | undefined,
): EditorialBriefPayload {
  if (!raw || Object.keys(raw).length === 0) {
    return emptyEditorialBriefPayload();
  }
  return {
    proposedTitle: String(raw.proposedTitle ?? ""),
    searchIntent: String(raw.searchIntent ?? ""),
    targetAudience: String(raw.targetAudience ?? ""),
    primaryKeyword: String(raw.primaryKeyword ?? ""),
    secondaryKeywords: coerceStringList(raw.secondaryKeywords),
    contentAngle: String(raw.contentAngle ?? ""),
    h2H3Structure: coerceStringList(raw.h2H3Structure),
    productsToLink: coerceStringList(raw.productsToLink),
    faqToInclude: coerceStringList(raw.faqToInclude),
    claimsToAvoid: coerceStringList(raw.claimsToAvoid),
    safeClaimsToUse: coerceStringList(raw.safeClaimsToUse),
    recommendedCta: String(raw.recommendedCta ?? ""),
    metaTitle: String(raw.metaTitle ?? ""),
    metaDescription: String(raw.metaDescription ?? ""),
    internalLinksSuggestions: coerceStringList(raw.internalLinksSuggestions),
    notes: String(raw.notes ?? ""),
    brandContextUsed: coerceStringList(raw.brandContextUsed),
    warnings: coerceStringList(raw.warnings),
  };
}

export function hasEditorialBrief(raw: Record<string, unknown> | null | undefined): boolean {
  if (!raw || Object.keys(raw).length === 0) return false;
  const parsed = parseEditorialBriefPayload(raw);
  return Boolean(
    parsed.proposedTitle.trim() ||
      parsed.primaryKeyword.trim() ||
      parsed.h2H3Structure.length > 0 ||
      parsed.metaTitle.trim(),
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
