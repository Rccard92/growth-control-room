import type { BriefH2Section, EditorialBriefPayload } from "@gcr/shared";

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
    authorSuggestion: "",
    authorReason: "",
    contentLengthProfile: "",
    communityCtaSuggestion: "",
    editorialToneNotes: [],
    recommendedWordCountMin: undefined,
    recommendedWordCountMax: undefined,
    structureComplexity: "",
    maxH2: undefined,
    maxH3: undefined,
    avoidRepetitions: [],
    editorialSkillChecklist: [],
    suggestedHtmlBlocks: [],
    internalLinkingPlan: [],
    readabilityNotes: [],
  };
}

const VALID_AUTHOR_SUGGESTIONS = new Set([
  "",
  "Davide",
  "Filippo Leonardi",
  "Salvo Leonardi",
]);

const VALID_LENGTH_PROFILES = new Set(["", "breve", "medio", "approfondito"]);
const VALID_STRUCTURE_COMPLEXITY = new Set(["", "snella", "media", "approfondita"]);

function coerceAuthorSuggestion(value: unknown): string {
  const text = String(value ?? "").trim();
  return VALID_AUTHOR_SUGGESTIONS.has(text) ? text : "";
}

function coerceLengthProfile(
  value: unknown,
): "" | "breve" | "medio" | "approfondito" {
  const text = String(value ?? "").trim();
  return VALID_LENGTH_PROFILES.has(text)
    ? (text as "" | "breve" | "medio" | "approfondito")
    : "";
}

function coerceStructureComplexity(
  value: unknown,
): "" | "snella" | "media" | "approfondita" {
  const text = String(value ?? "").trim();
  return VALID_STRUCTURE_COMPLEXITY.has(text)
    ? (text as "" | "snella" | "media" | "approfondita")
    : "";
}

function coerceOptionalInt(value: unknown): number | undefined {
  if (value === null || value === undefined || value === "") return undefined;
  const num = Number(value);
  return Number.isFinite(num) ? Math.round(num) : undefined;
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

function stripHeadingPrefix(text: string): string {
  return text.replace(/^h[23]\s*:\s*/i, "").trim();
}

export function coerceH2H3Structure(value: unknown): BriefH2Section[] {
  if (!value) return [];
  if (Array.isArray(value) && value.every((item) => item && typeof item === "object")) {
    return value
      .map((item) => {
        const record = item as Record<string, unknown>;
        const h2 = stripHeadingPrefix(String(record.h2 ?? ""));
        const h3Raw = record.h3;
        const h3 = Array.isArray(h3Raw)
          ? h3Raw.map((h) => stripHeadingPrefix(String(h))).filter(Boolean)
          : [];
        return h2 ? { h2, h3 } : null;
      })
      .filter((section): section is BriefH2Section => section !== null);
  }
  if (!Array.isArray(value)) return [];

  const sections: BriefH2Section[] = [];
  let current: BriefH2Section | null = null;
  for (const item of value) {
    const text = String(item ?? "").trim();
    if (!text) continue;
    if (/^h3\s*:/i.test(text)) {
      const h3 = stripHeadingPrefix(text);
      if (!h3) continue;
      if (!current) current = { h2: "", h3: [h3] };
      else current.h3.push(h3);
      continue;
    }
    if (/^h2\s*:/i.test(text) || !current || current.h2) {
      if (current?.h2) sections.push(current);
      current = { h2: stripHeadingPrefix(text), h3: [] };
    } else {
      current.h2 = stripHeadingPrefix(text);
    }
  }
  if (current?.h2) sections.push(current);
  return sections;
}

export function formatH2H3StructureForEditor(sections: BriefH2Section[]): string {
  const lines: string[] = [];
  for (const section of sections) {
    lines.push(`H2: ${section.h2}`);
    for (const h3 of section.h3) {
      lines.push(`  H3: ${h3}`);
    }
  }
  return lines.join("\n");
}

export function parseH2H3StructureFromEditor(text: string): BriefH2Section[] {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  return coerceH2H3Structure(lines);
}

export function formatStructureComplexityLabel(
  value: EditorialBriefPayload["structureComplexity"],
): string {
  switch (value) {
    case "snella":
      return "Snella";
    case "media":
      return "Media";
    case "approfondita":
      return "Approfondita";
    default:
      return "";
  }
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
    h2H3Structure: coerceH2H3Structure(raw.h2H3Structure),
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
    authorSuggestion: coerceAuthorSuggestion(raw.authorSuggestion),
    authorReason: String(raw.authorReason ?? ""),
    contentLengthProfile: coerceLengthProfile(raw.contentLengthProfile),
    communityCtaSuggestion: String(raw.communityCtaSuggestion ?? ""),
    editorialToneNotes: coerceStringList(raw.editorialToneNotes),
    recommendedWordCountMin: coerceOptionalInt(raw.recommendedWordCountMin),
    recommendedWordCountMax: coerceOptionalInt(raw.recommendedWordCountMax),
    structureComplexity: coerceStructureComplexity(raw.structureComplexity),
    maxH2: coerceOptionalInt(raw.maxH2),
    maxH3: coerceOptionalInt(raw.maxH3),
    avoidRepetitions: coerceStringList(raw.avoidRepetitions),
    editorialSkillChecklist: coerceStringList(raw.editorialSkillChecklist),
    suggestedHtmlBlocks: coerceStringList(raw.suggestedHtmlBlocks),
    internalLinkingPlan: coerceStringList(raw.internalLinkingPlan),
    readabilityNotes: coerceStringList(raw.readabilityNotes),
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
