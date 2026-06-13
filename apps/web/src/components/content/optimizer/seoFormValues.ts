import type {
  SeoCollectionDetailResponse,
  SeoProductDetailResponse,
  SeoScoreBreakdown,
} from "@gcr/shared";

export type SeoFormValues = Record<string, unknown>;

const PRODUCT_TITLE_KEYS = ["title", "product_title", "productTitle"];
const COLLECTION_TITLE_KEYS = ["title", "collection_title", "collectionTitle"];

function pickString(obj: Record<string, unknown>, keys: string[]): string {
  for (const k of keys) {
    const v = obj[k];
    if (typeof v === "string" && v.length > 0) return v;
  }
  return "";
}

function pickArray(obj: Record<string, unknown>, key: string): unknown[] {
  const v = obj[key];
  return Array.isArray(v) ? v : [];
}

function normalizeMediaItem(
  img: Record<string, unknown>,
  index: number,
): Record<string, unknown> {
  const alt =
    (typeof img.altText === "string" ? img.altText : null) ??
    (typeof img.alt === "string" ? img.alt : null) ??
    (typeof img.proposed_alt === "string" ? img.proposed_alt : null) ??
    "";
  return {
    ...img,
    id: img.id ?? img.image_id,
    altText: alt,
    position: typeof img.position === "number" ? img.position : index + 1,
  };
}

export function resolveMediaFromProposal(
  proposed: Record<string, unknown> | null | undefined,
  currentMedia: Record<string, unknown>[],
): Record<string, unknown>[] {
  if (!proposed) return currentMedia;

  const imageAlts = pickArray(proposed, "image_alts").length
    ? pickArray(proposed, "image_alts")
    : pickArray(proposed, "imageAlts");

  const proposedMedia = pickArray(proposed, "media_images").length
    ? pickArray(proposed, "media_images")
    : pickArray(proposed, "mediaImages");

  if (currentMedia.length === 0 && proposedMedia.length > 0) {
    return proposedMedia.map((item, idx) =>
      normalizeMediaItem(item as Record<string, unknown>, idx),
    );
  }

  if (currentMedia.length === 0) return currentMedia;

  const altById = new Map<string, string>();
  for (const entry of imageAlts) {
    const row = entry as Record<string, unknown>;
    const id = String(row.image_id ?? row.imageId ?? row.id ?? "");
    const alt = String(row.proposed_alt ?? row.proposedAlt ?? row.altText ?? row.alt ?? "");
    if (id && alt) altById.set(id, alt);
  }

  const proposedById = new Map<string, Record<string, unknown>>();
  for (const item of proposedMedia) {
    const row = item as Record<string, unknown>;
    const id = String(row.id ?? row.image_id ?? "");
    if (id) proposedById.set(id, row);
  }

  return currentMedia.map((img, idx) => {
    const id = String(img.id ?? "");
    const fromProposal = id ? proposedById.get(id) : undefined;
    const proposedAlt =
      (id ? altById.get(id) : undefined) ??
      (typeof fromProposal?.altText === "string" ? fromProposal.altText : undefined) ??
      (typeof fromProposal?.alt === "string" ? fromProposal.alt : undefined) ??
      (typeof fromProposal?.proposed_alt === "string" ? fromProposal.proposed_alt : undefined);

    if (!proposedAlt) return normalizeMediaItem(img, idx);
    return normalizeMediaItem({ ...img, altText: proposedAlt }, idx);
  });
}

export function buildImageAltsFromMedia(
  mediaImages: Record<string, unknown>[],
): Record<string, unknown>[] {
  const rows: Record<string, unknown>[] = []
  for (const img of mediaImages) {
    const id = img.id
    const alt = img.altText ?? img.alt
    if (!id || !alt || (typeof alt === "string" && !alt.trim())) continue
    rows.push({
      image_id: id,
      current_alt: img.altText ?? img.alt ?? "",
      proposed_alt: alt,
    })
  }
  return rows
}

export function normalizeFormValues(
  raw: Record<string, unknown> | null | undefined,
  entityType: "product" | "collection",
  detail?: SeoProductDetailResponse | SeoCollectionDetailResponse | null,
): SeoFormValues {
  const src = raw ?? {};

  if (entityType === "product") {
    const productDetail = detail as SeoProductDetailResponse | null | undefined;
    const nested = productDetail?.product as Record<string, unknown> | undefined;

    const rawImages =
      pickArray(src, "images").length > 0
        ? pickArray(src, "images")
        : pickArray(src, "media_images").length > 0
          ? pickArray(src, "media_images")
          : (productDetail?.images ?? []);

    const images = rawImages.map((item, idx) =>
      normalizeMediaItem(item as Record<string, unknown>, idx),
    );

    return {
      title:
        pickString(src, PRODUCT_TITLE_KEYS) ||
        (typeof nested?.title === "string" ? nested.title : ""),
      handle: pickString(src, ["handle"]) || (typeof nested?.handle === "string" ? nested.handle : ""),
      seoTitle: pickString(src, ["seoTitle", "seo_title"]),
      metaDescription: pickString(src, ["metaDescription", "meta_description"]),
      descriptionHtml: pickString(src, ["descriptionHtml", "description_html"]),
      descriptionText: pickString(src, ["descriptionText", "description_text"]),
      productType:
        pickString(src, ["productType", "product_type"]) ||
        (typeof nested?.product_type === "string" ? nested.product_type : ""),
      vendor:
        pickString(src, ["vendor"]) ||
        (typeof nested?.vendor === "string" ? nested.vendor : ""),
      images,
    };
  }

  const collectionDetail = detail as SeoCollectionDetailResponse | null | undefined;
  const nested = collectionDetail?.collection as Record<string, unknown> | undefined;

  const imageAlt =
    pickString(src, ["imageAlt", "image_alt"]) ||
    (typeof collectionDetail?.image?.alt === "string" ? collectionDetail.image.alt : "");

  return {
    title:
      pickString(src, COLLECTION_TITLE_KEYS) ||
      (typeof nested?.title === "string" ? nested.title : ""),
    handle: pickString(src, ["handle"]) || (typeof nested?.handle === "string" ? nested.handle : ""),
    seoTitle: pickString(src, ["seoTitle", "seo_title"]),
    metaDescription: pickString(src, ["metaDescription", "meta_description"]),
    descriptionHtml: pickString(src, ["descriptionHtml", "description_html"]),
    descriptionText: pickString(src, ["descriptionText", "description_text"]),
    imageAlt,
    images: collectionDetail?.image ? [collectionDetail.image] : [],
  };
}

/** Convert form camelCase to snake_case for proposal API */
export function toProposalValues(
  form: SeoFormValues,
  entityType: "product" | "collection",
  mediaImages?: Record<string, unknown>[],
): Record<string, unknown> {
  if (entityType === "product") {
    const media = (mediaImages ?? (form.images as Record<string, unknown>[] | undefined) ?? []).map(
      (img, idx) => normalizeMediaItem(img, idx),
    );
    const result: Record<string, unknown> = {
      product_title: form.title,
      handle: form.handle,
      seo_title: form.seoTitle,
      meta_description: form.metaDescription,
      description_html: form.descriptionHtml,
      description_text: form.descriptionText,
      media_images: media,
    };
    const imageAlts = buildImageAltsFromMedia(media);
    if (imageAlts.length > 0) {
      result.image_alts = imageAlts;
    }
    return result;
  }
  return {
    collection_title: form.title,
    handle: form.handle,
    seo_title: form.seoTitle,
    meta_description: form.metaDescription,
    description_html: form.descriptionHtml,
    description_text: form.descriptionText,
    image_alt: form.imageAlt,
  };
}

/** Merge AI/proposal values (any casing) into camelCase form */
export function mergeProposedIntoForm(
  current: SeoFormValues,
  proposed: Record<string, unknown> | null | undefined,
  entityType: "product" | "collection",
): SeoFormValues {
  if (!proposed) return { ...current };
  const normalized = normalizeFormValues(proposed, entityType);
  const merged = { ...current };
  for (const [key, val] of Object.entries(normalized)) {
    if (val === undefined || val === null) continue;
    if (typeof val === "string" && val === "" && key !== "title") continue;
    if (Array.isArray(val) && val.length === 0 && key !== "images") continue;
    merged[key] = val;
  }
  if (entityType === "product") {
    const currentImages = (current.images as Record<string, unknown>[] | undefined) ?? [];
    merged.images = resolveMediaFromProposal(proposed, currentImages);
  }
  return merged;
}

export type FieldStatus = "ok" | "missing" | "improve";

const ISSUE_FIELD_MAP: Record<string, string[]> = {
  title: ["title", "product_title", "collection_title"],
  handle: ["handle"],
  seoTitle: ["seo_title", "seoTitle"],
  metaDescription: ["seo_description", "metaDescription", "meta_description"],
  descriptionHtml: ["description", "description_html", "descriptionHtml"],
  imageAlt: ["image_alt", "media_images", "imageAlt"],
  productType: ["product_type", "productType"],
  vendor: ["vendor"],
};

const MISSING_ISSUE_CODES = new Set([
  "missing_seo_title",
  "missing_meta_description",
  "missing_description",
  "missing_image_alt",
  "weak_title",
]);

function isEmptyValue(value: unknown): boolean {
  if (value == null) return true;
  if (typeof value === "string") return value.trim() === "";
  if (Array.isArray(value)) return value.length === 0;
  return false;
}

function fieldHasValue(
  field: string,
  formValues: SeoFormValues,
  mediaImages?: Record<string, unknown>[],
): boolean {
  if (field === "imageAlt") {
    const media = mediaImages ?? (formValues.images as Record<string, unknown>[] | undefined) ?? [];
    if (media.length === 0) return false;
    return media.every((img) => {
      const alt = img.altText ?? img.alt;
      return typeof alt === "string" && alt.trim().length > 0;
    });
  }
  const keyMap: Record<string, string> = {
    title: "title",
    handle: "handle",
    seoTitle: "seoTitle",
    metaDescription: "metaDescription",
    descriptionHtml: "descriptionHtml",
  };
  const key = keyMap[field] ?? field;
  return !isEmptyValue(formValues[key]);
}

export function getEffectiveIssues(
  issues: Record<string, unknown>[] | null | undefined,
  formValues: SeoFormValues,
  mediaImages?: Record<string, unknown>[],
): Record<string, unknown>[] {
  return (issues ?? []).filter((issue) => {
    const code = String(issue.code ?? "");
    const field = String(issue.field ?? "");
    if (!MISSING_ISSUE_CODES.has(code) && !code.startsWith("missing_")) {
      return true;
    }
    const formField =
      field === "seo_title"
        ? "seoTitle"
        : field === "seo_description"
          ? "metaDescription"
          : field === "description"
            ? "descriptionHtml"
            : field === "media_images" || field === "image_alt"
              ? "imageAlt"
              : field === "product_title" || field === "collection_title"
                ? "title"
                : field;
    return !fieldHasValue(formField, formValues, mediaImages);
  });
}

function findIssueForField(
  field: string,
  issues?: Record<string, unknown>[] | null,
): Record<string, unknown> | undefined {
  const aliases = ISSUE_FIELD_MAP[field] ?? [field];
  return (issues ?? []).find((issue) => {
    const f = String(issue.field ?? "");
    return aliases.includes(f);
  });
}

function breakdownScoreForField(
  field: string,
  scoreBreakdown?: SeoScoreBreakdown | null,
): number | null {
  if (!scoreBreakdown) return null;
  const keyMap: Record<string, string> = {
    title: "title",
    seoTitle: "seoTitle",
    metaDescription: "metaDescription",
    descriptionHtml: "description",
    handle: "handle",
    imageAlt: "imageAlt",
  };
  const bk = keyMap[field];
  if (!bk || !scoreBreakdown[bk]) return null;
  const item = scoreBreakdown[bk];
  if (item.max <= 0) return null;
  return Math.round((item.score / item.max) * 100);
}

export function getFieldStatus(
  field: string,
  value: unknown,
  issues?: Record<string, unknown>[] | null,
  scoreBreakdown?: SeoScoreBreakdown | null,
): { status: FieldStatus; note?: string } {
  if (isEmptyValue(value)) {
    return { status: "missing", note: "Campo non impostato su Shopify" };
  }

  const issue = findIssueForField(field, issues);
  if (issue) {
    const sev = String(issue.severity ?? "");
    if (sev === "critical" || sev === "warning" || sev === "opportunity") {
      return {
        status: "improve",
        note: String(issue.message ?? "Campo da migliorare"),
      };
    }
  }

  const pct = breakdownScoreForField(field, scoreBreakdown);
  if (pct != null && pct < 80) {
    return { status: "improve", note: "Score componente sotto soglia ottimale" };
  }

  return { status: "ok" };
}
