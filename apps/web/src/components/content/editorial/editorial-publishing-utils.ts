import type {
  EditorialArticlePayload,
  EditorialPublishingPayload,
  EditorialPublishMode,
} from "@gcr/shared";

export const DEFAULT_AUTHOR_FALLBACK = "Redazione Solmielato";
export const SEO_TITLE_MAX = 60;
export const META_DESCRIPTION_MAX = 160;
export const SEO_REQUIRED_MESSAGE =
  "SEO title e meta description sono obbligatori per creare un articolo Shopify completo.";

export function emptyEditorialPublishingPayload(): EditorialPublishingPayload {
  return {
    title: "",
    handle: "",
    bodyHtml: "",
    excerpt: "",
    seoTitle: "",
    metaDescription: "",
    author: "",
    blogId: null,
    blogGid: null,
    tags: [],
    imageUrl: null,
    imageAlt: null,
    mode: "draft",
    isPublished: false,
    publishDate: null,
    templateSuffix: null,
    sourceArticleHash: null,
    sourceArticleUpdatedAt: null,
    syncedFromArticleAt: null,
    shopifySeoSynced: null,
    shopifySeoSyncedAt: null,
    shopifySeoError: null,
  };
}

function coerceTags(value: unknown): string[] {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.map((v) => String(v).trim()).filter(Boolean);
  }
  if (typeof value === "string") {
    return value
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean);
  }
  return [];
}

export function resolveDefaultAuthor(options?: {
  articleAuthorName?: string | null;
  savedAuthor?: string | null;
  shopName?: string | null;
  brandName?: string | null;
}): string {
  const candidates = [
    options?.articleAuthorName,
    options?.savedAuthor,
    options?.shopName,
    options?.brandName,
    options?.brandName ? `Redazione ${options.brandName}` : null,
    DEFAULT_AUTHOR_FALLBACK,
  ];
  for (const candidate of candidates) {
    if (candidate && String(candidate).trim()) {
      return String(candidate).trim();
    }
  }
  return DEFAULT_AUTHOR_FALLBACK;
}

export function parseEditorialPublishingPayload(
  raw: Record<string, unknown> | EditorialPublishingPayload | null | undefined,
): EditorialPublishingPayload {
  if (!raw || Object.keys(raw).length === 0) {
    return emptyEditorialPublishingPayload();
  }
  const mode = raw.mode;
  const normalizedMode: EditorialPublishMode =
    mode === "publish_now" || mode === "schedule" ? mode : "draft";
  return {
    title: String(raw.title ?? ""),
    handle: String(raw.handle ?? ""),
    bodyHtml: String(raw.bodyHtml ?? ""),
    excerpt: String(raw.excerpt ?? ""),
    seoTitle: String(raw.seoTitle ?? ""),
    metaDescription: String(raw.metaDescription ?? ""),
    author: String(raw.author ?? ""),
    blogId: raw.blogId ? String(raw.blogId) : null,
    blogGid: raw.blogGid ? String(raw.blogGid) : null,
    tags: coerceTags(raw.tags),
    imageUrl: raw.imageUrl ? String(raw.imageUrl) : null,
    imageAlt: raw.imageAlt ? String(raw.imageAlt) : null,
    mode: normalizedMode,
    isPublished: Boolean(raw.isPublished),
    publishDate: raw.publishDate ? String(raw.publishDate) : null,
    templateSuffix: raw.templateSuffix ? String(raw.templateSuffix) : null,
    sourceArticleHash: raw.sourceArticleHash ? String(raw.sourceArticleHash) : null,
    sourceArticleUpdatedAt: raw.sourceArticleUpdatedAt
      ? String(raw.sourceArticleUpdatedAt)
      : null,
    syncedFromArticleAt: raw.syncedFromArticleAt ? String(raw.syncedFromArticleAt) : null,
    shopifySeoSynced:
      raw.shopifySeoSynced === undefined || raw.shopifySeoSynced === null
        ? null
        : Boolean(raw.shopifySeoSynced),
    shopifySeoSyncedAt: raw.shopifySeoSyncedAt ? String(raw.shopifySeoSyncedAt) : null,
    shopifySeoError: raw.shopifySeoError ? String(raw.shopifySeoError) : null,
  };
}

export function buildArticleHashCanonical(article: EditorialArticlePayload): string {
  const tags = [...(article.tags ?? [])]
    .map((t) => String(t).trim())
    .filter(Boolean)
    .sort()
    .join(",");
  const payload = {
    title: article.title.trim(),
    handle: article.handle.trim(),
    bodyHtml: article.bodyHtml.trim(),
    excerpt: article.excerpt.trim(),
    seoTitle: article.seoTitle.trim(),
    metaDescription: article.metaDescription.trim(),
    tags,
    authorName: (article.authorName ?? "").trim(),
  };
  return JSON.stringify(payload);
}

export function isPublishingStale(
  article: EditorialArticlePayload | null | undefined,
  publishing: EditorialPublishingPayload | null | undefined,
): boolean {
  if (!article || !publishing) return false;
  const sourceHash = publishing.sourceArticleHash?.trim();
  const articleHash = article.articleHash?.trim();
  if (!sourceHash || !articleHash) return true;
  return sourceHash !== articleHash;
}

/** @deprecated Use isPublishingStale — legacy payloads without hash are now treated as stale. */
export function isPublishingSyncUnknown(
  article: EditorialArticlePayload | null | undefined,
  publishing: EditorialPublishingPayload | null | undefined,
  hasSavedPublishing: boolean,
): boolean {
  if (!article || !publishing || !hasSavedPublishing) return false;
  return isPublishingStale(article, publishing);
}

export function buildPublishingPayloadFromArticle(
  article: EditorialArticlePayload,
  options?: {
    blogId?: string | null;
    blogGid?: string | null;
    shopName?: string | null;
    brandName?: string | null;
    savedAuthor?: string | null;
  },
): EditorialPublishingPayload {
  const author = resolveDefaultAuthor({
    articleAuthorName: article.authorName,
    savedAuthor: options?.savedAuthor,
    shopName: options?.shopName,
    brandName: options?.brandName,
  });
  return {
    title: article.title.trim(),
    handle: article.handle.trim(),
    bodyHtml: article.bodyHtml.trim(),
    excerpt: article.excerpt.trim(),
    seoTitle: article.seoTitle.trim() || article.title.trim(),
    metaDescription: article.metaDescription.trim(),
    author,
    blogId: options?.blogId ?? null,
    blogGid: options?.blogGid ?? null,
    tags: [...(article.tags ?? [])],
    imageUrl: null,
    imageAlt: null,
    mode: "draft",
    isPublished: false,
    publishDate: null,
    templateSuffix: null,
  };
}

export function getPublishingSeoWarnings(payload: EditorialPublishingPayload): string[] {
  const warnings: string[] = [];
  const seoTitle = payload.seoTitle.trim();
  const metaDescription = payload.metaDescription.trim();
  if (seoTitle.length > SEO_TITLE_MAX) {
    warnings.push(
      `SEO title lungo (${seoTitle.length} caratteri; consigliati max ${SEO_TITLE_MAX}).`,
    );
  }
  if (metaDescription.length > META_DESCRIPTION_MAX) {
    warnings.push(
      `Meta description lunga (${metaDescription.length} caratteri; consigliati max ${META_DESCRIPTION_MAX}).`,
    );
  }
  return warnings;
}

export function isPublishingSeoComplete(payload: EditorialPublishingPayload | null | undefined): boolean {
  if (!payload) return false;
  return Boolean(payload.seoTitle.trim() && payload.metaDescription.trim() && payload.handle.trim());
}

export function validatePublishingPayload(
  payload: EditorialPublishingPayload,
  options?: { forPublish?: boolean },
): string[] {
  const errors: string[] = [];
  if (!payload.title.trim()) errors.push("Il titolo è obbligatorio.");
  if (!payload.bodyHtml.trim()) errors.push("Il contenuto HTML è obbligatorio.");
  if (options?.forPublish && !payload.blogId && !payload.blogGid) {
    errors.push("Seleziona un blog Shopify prima di pubblicare.");
  }
  if (options?.forPublish && !payload.author.trim()) {
    errors.push("Autore obbligatorio per creare l'articolo su Shopify.");
  }
  if (options?.forPublish) {
    if (!payload.seoTitle.trim() || !payload.metaDescription.trim()) {
      errors.push(SEO_REQUIRED_MESSAGE);
    }
    if (!payload.handle.trim()) {
      errors.push("Handle obbligatorio per pubblicare su Shopify.");
    }
  }
  return errors;
}

export function validatePublishingPayloadWithWarnings(
  payload: EditorialPublishingPayload,
  options?: { forPublish?: boolean },
): { errors: string[]; warnings: string[] } {
  return {
    errors: validatePublishingPayload(payload, options),
    warnings: options?.forPublish ? getPublishingSeoWarnings(payload) : [],
  };
}

export function tagsToInput(tags: string[]): string {
  return tags.join(", ");
}

export function inputToTags(value: string): string[] {
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

export function getPublishStatusLabel(status?: string | null): string {
  switch (status) {
    case "draft_created":
      return "Bozza su Shopify";
    case "published":
      return "Pubblicato";
    case "publish_error":
      return "Errore";
    case "scheduled":
      return "Programmato";
    default:
      return "Non pubblicato";
  }
}

export function extractApiErrorMessage(error: unknown): string | null {
  if (!(error instanceof Error)) return null;
  const detail = error.message.trim();
  if (!detail || detail === "Failed to fetch") return null;
  return detail;
}

export function formatPublishingError(baseMessage: string, error: unknown): string {
  const detail = extractApiErrorMessage(error);
  if (!detail) return baseMessage;
  let message = `${baseMessage} ${detail}`;
  if (message.includes("Field 'seo'") || message.includes("Field `seo`")) {
    message +=
      " Il publisher sta ancora usando un campo GraphQL non supportato. Controllare query Shopify.";
  }
  return message;
}

export function parseStructuredPublishErrorDetail(
  detail: unknown,
): { message: string; code?: string } | null {
  if (!detail || typeof detail !== "object" || Array.isArray(detail)) return null;
  const record = detail as Record<string, unknown>;
  if (typeof record.message === "string") {
    return {
      message: record.message,
      code: typeof record.code === "string" ? record.code : undefined,
    };
  }
  return null;
}
