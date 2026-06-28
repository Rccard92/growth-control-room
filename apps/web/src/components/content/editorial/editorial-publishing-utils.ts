import type {
  EditorialArticlePayload,
  EditorialPublishingPayload,
  EditorialPublishMode,
} from "@gcr/shared";

export const DEFAULT_AUTHOR_FALLBACK = "Redazione Solmielato";

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
  if (!sourceHash || !articleHash) return false;
  return sourceHash !== articleHash;
}

export function isPublishingSyncUnknown(
  article: EditorialArticlePayload | null | undefined,
  publishing: EditorialPublishingPayload | null | undefined,
  hasSavedPublishing: boolean,
): boolean {
  if (!article || !publishing || !hasSavedPublishing) return false;
  return !publishing.sourceArticleHash?.trim() || !article.articleHash?.trim();
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
  return errors;
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
