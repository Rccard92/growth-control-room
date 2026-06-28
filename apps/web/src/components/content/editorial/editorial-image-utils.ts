import type { EditorialImagePayload, EditorialImageStatus } from "@gcr/shared";

export const IMAGE_STALE_MESSAGE =
  "L'immagine potrebbe non essere aggiornata rispetto all'ultima versione dell'articolo.";

export const IMAGE_STALE_PUBLISH_WARNING =
  "L'immagine approvata potrebbe non essere allineata all'ultima versione dell'articolo.";

export const NO_APPROVED_IMAGE_WARNING = "Nessuna immagine approvata associata all'articolo.";

export const PUBLIC_STORAGE_WARNING =
  "Storage pubblico immagini non configurato: l'immagine non può essere inviata a Shopify.";

export const FILENAME_STALE_MESSAGE =
  "Il titolo articolo è cambiato: il nome file SEO potrebbe non essere più allineato.";

const STATUS_LABELS: Record<EditorialImageStatus, string> = {
  not_generated: "Non generata",
  generated: "Generata",
  approved: "Approvata",
};

export function getImageStatusLabel(status: EditorialImageStatus | undefined): string {
  if (!status) return STATUS_LABELS.not_generated;
  return STATUS_LABELS[status] ?? status;
}

export function formatImageCost(cost: number | null | undefined): string {
  if (cost == null || Number.isNaN(cost)) return "—";
  return `$${cost.toFixed(4)}`;
}

export function formatImageUpdatedAt(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("it-IT");
}

export function formatImageDimensions(image: EditorialImagePayload): string {
  if (image.imageWidth && image.imageHeight) {
    return `${image.imageWidth}×${image.imageHeight}`;
  }
  return "1600×900";
}

export function emptyEditorialImagePayload(): EditorialImagePayload {
  return { imageStatus: "not_generated", imagePrompt: "" };
}

export function parseEditorialImagePayload(
  raw: EditorialImagePayload | Record<string, unknown> | null | undefined,
): EditorialImagePayload {
  if (!raw || typeof raw !== "object") return emptyEditorialImagePayload();
  const record = raw as Record<string, unknown>;
  const status = (record.imageStatus ?? record.image_status ?? "not_generated") as EditorialImageStatus;
  return {
    imageStatus: status === "generated" || status === "approved" ? status : "not_generated",
    imagePrompt: String(record.imagePrompt ?? record.image_prompt ?? ""),
    imageRevisionNote: (record.imageRevisionNote ?? record.image_revision_note ?? null) as string | null,
    imageModel: (record.imageModel ?? record.image_model ?? null) as string | null,
    imageAlt: (record.imageAlt ?? record.image_alt ?? null) as string | null,
    imageUrl: (record.imageUrl ?? record.image_url ?? null) as string | null,
    imageStoragePath: (record.imageStoragePath ?? record.image_storage_path ?? null) as string | null,
    imageFilename: (record.imageFilename ?? record.image_filename ?? null) as string | null,
    imageOriginalProviderFilename: (record.imageOriginalProviderFilename ??
      record.image_original_provider_filename ??
      null) as string | null,
    imageWidth: (record.imageWidth ?? record.image_width ?? null) as number | null,
    imageHeight: (record.imageHeight ?? record.image_height ?? null) as number | null,
    imageAspectRatio: (record.imageAspectRatio ?? record.image_aspect_ratio ?? null) as string | null,
    imageMimeType: (record.imageMimeType ?? record.image_mime_type ?? null) as string | null,
    imageFileExtension: (record.imageFileExtension ?? record.image_file_extension ?? null) as string | null,
    imageGenerationCost: (record.imageGenerationCost ?? record.image_generation_cost ?? null) as number | null,
    imageGenerationLogId: (record.imageGenerationLogId ?? record.image_generation_log_id ?? null) as string | null,
    imageApprovedAt: (record.imageApprovedAt ?? record.image_approved_at ?? null) as string | null,
    imageHash: (record.imageHash ?? record.image_hash ?? null) as string | null,
    sourceArticleHash: (record.sourceArticleHash ?? record.source_article_hash ?? null) as string | null,
    accessToken: (record.accessToken ?? record.access_token ?? null) as string | null,
    updatedAt: (record.updatedAt ?? record.updated_at ?? null) as string | null,
    skillPackUsed: String(record.skillPackUsed ?? record.skill_pack_used ?? ""),
    skillPackVersion: String(record.skillPackVersion ?? record.skill_pack_version ?? ""),
    shopifyImageReady: Boolean(record.shopifyImageReady ?? record.shopify_image_ready ?? false),
    shopifyImageSyncedAt: (record.shopifyImageSyncedAt ?? record.shopify_image_synced_at ?? null) as string | null,
    shopifyImageAltSynced: (record.shopifyImageAltSynced ?? record.shopify_image_alt_synced ?? null) as string | null,
    shopifyImageFilenameSynced: (record.shopifyImageFilenameSynced ??
      record.shopify_image_filename_synced ??
      null) as string | null,
    approvedImageBackup: (record.approvedImageBackup ?? record.approved_image_backup ?? null) as EditorialImagePayload["approvedImageBackup"],
    aiGeneration: (record.aiGeneration ?? record.ai_generation ?? undefined) as EditorialImagePayload["aiGeneration"],
  };
}

export function hasGeneratedImage(image: EditorialImagePayload): boolean {
  return image.imageStatus === "generated" || image.imageStatus === "approved";
}

export function isImageFilenameStale(image: EditorialImagePayload, articleTitle: string): boolean {
  if (!image.imageFilename || !articleTitle.trim()) return false;
  const slugify = (value: string) =>
    value
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  const titleSlug = slugify(articleTitle).slice(0, 90);
  const fileSlug = image.imageFilename.replace(/\.jpe?g$/i, "").toLowerCase();
  const baseFile = fileSlug.replace(/-v\d+$/, "").replace(/-[a-f0-9]{6}$/, "");
  return baseFile !== titleSlug && fileSlug !== titleSlug;
}

export function hasApprovedImageForPublish(image: EditorialImagePayload): boolean {
  if (image.imageStatus === "approved") return true;
  return image.imageStatus === "generated" && Boolean(image.approvedImageBackup);
}
