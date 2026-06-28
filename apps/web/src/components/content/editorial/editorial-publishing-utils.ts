import type {
  EditorialArticlePayload,
  EditorialPublishingPayload,
  EditorialPublishMode,
} from "@gcr/shared";

export const DEFAULT_AUTHOR_FALLBACK = "Redazione Solmielato";
export const DEFAULT_EDITORIAL_PUBLISH_TIME = "09:00";
export const DEFAULT_EDITORIAL_TIMEZONE = "Europe/Rome";
export const PED_PAST_DATE_WARNING =
  "La data PED è passata. Crea bozza o scegli una nuova data.";
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
    scheduledPublishAt: null,
    scheduledPublishTimezone: null,
    scheduledPublishSource: null,
    sourcePlannedDate: null,
    scheduledPublishTime: DEFAULT_EDITORIAL_PUBLISH_TIME,
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
    scheduledPublishAt: raw.scheduledPublishAt ? String(raw.scheduledPublishAt) : null,
    scheduledPublishTimezone: raw.scheduledPublishTimezone
      ? String(raw.scheduledPublishTimezone)
      : null,
    scheduledPublishSource:
      raw.scheduledPublishSource === "manual" || raw.scheduledPublishSource === "ped_planned_date"
        ? raw.scheduledPublishSource
        : null,
    sourcePlannedDate: raw.sourcePlannedDate ? String(raw.sourcePlannedDate) : null,
    scheduledPublishTime: raw.scheduledPublishTime
      ? String(raw.scheduledPublishTime)
      : DEFAULT_EDITORIAL_PUBLISH_TIME,
  };
}

export type PlannedDateClass = "future" | "today" | "past";

export function resolveEditorialTimezone(timezone?: string | null): string {
  const tz = timezone?.trim();
  return tz || DEFAULT_EDITORIAL_TIMEZONE;
}

function dateKeyInTimezone(date: Date, timezone: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

export function classifyPlannedDate(
  plannedDate: string,
  timezone: string,
): PlannedDateClass {
  const todayKey = dateKeyInTimezone(new Date(), timezone);
  const plannedKey = plannedDate.slice(0, 10);
  if (plannedKey > todayKey) return "future";
  if (plannedKey === todayKey) return "today";
  return "past";
}

function getTimezoneOffsetMinutes(timezone: string, at: Date): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: timezone,
    timeZoneName: "shortOffset",
  }).formatToParts(at);
  const tzName = parts.find((part) => part.type === "timeZoneName")?.value ?? "GMT";
  const match = tzName.match(/GMT([+-])(\d{1,2})(?::(\d{2}))?/);
  if (!match) return 0;
  const sign = match[1] === "-" ? -1 : 1;
  const hours = Number(match[2]);
  const minutes = Number(match[3] ?? "0");
  return sign * (hours * 60 + minutes);
}

export function buildScheduledPublishAt(
  plannedDate: string,
  publishTime: string,
  timezone: string,
): string {
  const dateKey = plannedDate.slice(0, 10);
  const time = publishTime.trim() || DEFAULT_EDITORIAL_PUBLISH_TIME;
  const [year, month, day] = dateKey.split("-").map(Number);
  const [hour, minute] = time.split(":").map(Number);
  const probe = new Date(Date.UTC(year, month - 1, day, hour, minute));
  const offsetMinutes = getTimezoneOffsetMinutes(timezone, probe);
  const sign = offsetMinutes >= 0 ? "+" : "-";
  const abs = Math.abs(offsetMinutes);
  const offsetStr = `${sign}${String(Math.floor(abs / 60)).padStart(2, "0")}:${String(abs % 60).padStart(2, "0")}`;
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}T${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}:00${offsetStr}`;
}

export function applyPedScheduleDefaults(
  publishing: EditorialPublishingPayload,
  options: {
    plannedDate: string;
    timezone?: string | null;
    publishTime?: string | null;
    force?: boolean;
  },
): EditorialPublishingPayload {
  const timezone = resolveEditorialTimezone(options.timezone ?? publishing.scheduledPublishTimezone);
  const publishTime = options.publishTime?.trim() || publishing.scheduledPublishTime || DEFAULT_EDITORIAL_PUBLISH_TIME;
  if (!options.force && publishing.scheduledPublishSource === "manual") {
    return publishing;
  }
  const classification = classifyPlannedDate(options.plannedDate, timezone);
  if (classification === "future") {
    const scheduledAt = buildScheduledPublishAt(options.plannedDate, publishTime, timezone);
    return {
      ...publishing,
      mode: "schedule",
      scheduledPublishAt: scheduledAt,
      scheduledPublishTimezone: timezone,
      scheduledPublishSource: "ped_planned_date",
      sourcePlannedDate: options.plannedDate.slice(0, 10),
      scheduledPublishTime: publishTime,
      publishDate: scheduledAt,
      isPublished: true,
    };
  }
  return {
    ...publishing,
    mode: "draft",
    scheduledPublishAt: null,
    scheduledPublishTimezone: timezone,
    scheduledPublishSource: "ped_planned_date",
    sourcePlannedDate: options.plannedDate.slice(0, 10),
    scheduledPublishTime: publishTime,
    publishDate: null,
    isPublished: false,
  };
}

export function getScheduleDateFromPublishing(
  publishing: EditorialPublishingPayload,
  plannedDate: string,
): string {
  if (publishing.scheduledPublishAt) {
    return publishing.scheduledPublishAt.slice(0, 10);
  }
  return publishing.sourcePlannedDate?.slice(0, 10) || plannedDate.slice(0, 10);
}

export function formatPlannedDateItalian(plannedDate: string): string {
  const [year, month, day] = plannedDate.slice(0, 10).split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  return new Intl.DateTimeFormat("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

export function formatPedScheduleMessage(
  plannedDate: string,
  publishTime: string,
  timezone: string,
): string {
  const classification = classifyPlannedDate(plannedDate, timezone);
  const plannedLabel = formatPlannedDateItalian(plannedDate);
  if (classification === "future") {
    return `Questo articolo è previsto nel PED per il ${plannedLabel}. Verrà programmato su Shopify per il ${plannedLabel} alle ${publishTime}.`;
  }
  if (classification === "today") {
    return `Questo articolo è previsto nel PED per oggi (${plannedLabel}). Di default verrà creata una bozza Shopify.`;
  }
  return PED_PAST_DATE_WARNING;
}

export interface PrimaryPublishAction {
  mode: EditorialPublishMode;
  label: string;
  confirmMessage?: string;
}

export function getPrimaryPublishAction(options: {
  plannedDate: string;
  timezone: string;
  publishingStale: boolean;
  hasShopifyLink: boolean;
  isPublishedOnShopify: boolean;
}): PrimaryPublishAction {
  const classification = classifyPlannedDate(options.plannedDate, options.timezone);
  if (options.publishingStale && classification === "future") {
    return { mode: "schedule", label: "Aggiorna dati e programma su Shopify" };
  }
  if (classification === "future") {
    return {
      mode: "schedule",
      label: options.hasShopifyLink
        ? "Aggiorna programmazione Shopify"
        : "Programma su Shopify",
    };
  }
  if (classification === "today") {
    return {
      mode: "publish_now",
      label: options.isPublishedOnShopify
        ? "Aggiorna articolo pubblicato"
        : options.hasShopifyLink
          ? "Pubblica bozza Shopify"
          : "Pubblica subito",
      confirmMessage: options.isPublishedOnShopify
        ? "Aggiornare l'articolo già pubblicato su Shopify con i dati attuali?"
        : options.hasShopifyLink
          ? "Pubblicare la bozza Shopify collegata? Sarà visibile nel blog selezionato."
          : "Pubblicare subito questo articolo su Shopify? Sarà visibile nel blog selezionato.",
    };
  }
  return {
    mode: "draft",
    label: options.hasShopifyLink ? "Aggiorna bozza Shopify" : "Crea bozza Shopify",
  };
}

export function formatScheduledPublishLabel(
  scheduledAt: string | null | undefined,
  timezone?: string | null,
): string {
  if (!scheduledAt) return "Programmato Shopify";
  const date = new Date(scheduledAt);
  if (Number.isNaN(date.getTime())) return "Programmato Shopify";
  const formatted = new Intl.DateTimeFormat("it-IT", {
    timeZone: resolveEditorialTimezone(timezone),
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
  return `Programmato ${formatted}`;
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
    plannedDate?: string;
    timezone?: string | null;
  },
): EditorialPublishingPayload {
  const author = resolveDefaultAuthor({
    articleAuthorName: article.authorName,
    savedAuthor: options?.savedAuthor,
    shopName: options?.shopName,
    brandName: options?.brandName,
  });
  const base: EditorialPublishingPayload = {
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
  if (options?.plannedDate) {
    return applyPedScheduleDefaults(base, {
      plannedDate: options.plannedDate,
      timezone: options.timezone,
    });
  }
  return base;
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
    if (payload.mode === "schedule" && !payload.scheduledPublishAt) {
      errors.push("Data di pubblicazione programmata obbligatoria.");
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
      return "Programmato Shopify";
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
