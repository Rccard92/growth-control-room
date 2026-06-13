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

export function normalizeFormValues(
  raw: Record<string, unknown> | null | undefined,
  entityType: "product" | "collection",
  detail?: SeoProductDetailResponse | SeoCollectionDetailResponse | null,
): SeoFormValues {
  const src = raw ?? {};

  if (entityType === "product") {
    const productDetail = detail as SeoProductDetailResponse | null | undefined;
    const nested = productDetail?.product as Record<string, unknown> | undefined;

    const images =
      pickArray(src, "images").length > 0
        ? pickArray(src, "images")
        : pickArray(src, "media_images").length > 0
          ? pickArray(src, "media_images")
          : (productDetail?.images ?? []);

    return {
      title:
        pickString(src, PRODUCT_TITLE_KEYS) ||
        (typeof nested?.title === "string" ? nested.title : ""),
      handle: pickString(src, ["handle"]) || (typeof nested?.handle === "string" ? nested.handle : ""),
      seoTitle: pickString(src, ["seoTitle", "seo_title"]),
      metaDescription: pickString(src, ["metaDescription", "meta_description"]),
      descriptionHtml: pickString(src, ["descriptionHtml", "description_html"]),
      descriptionText: pickString(src, ["descriptionText", "description_text"]),
      tags: Array.isArray(src.tags) ? src.tags : [],
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
    return {
      product_title: form.title,
      handle: form.handle,
      seo_title: form.seoTitle,
      meta_description: form.metaDescription,
      description_html: form.descriptionHtml,
      description_text: form.descriptionText,
      tags: form.tags,
      media_images: mediaImages ?? form.images,
    };
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
    if (Array.isArray(val) && val.length === 0) continue;
    merged[key] = val;
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
  tags: ["tags"],
  imageAlt: ["image_alt", "media_images", "imageAlt"],
  productType: ["product_type", "productType"],
  vendor: ["vendor"],
};

function isEmptyValue(value: unknown): boolean {
  if (value == null) return true;
  if (typeof value === "string") return value.trim() === "";
  if (Array.isArray(value)) return value.length === 0;
  return false;
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
    tags: "tags",
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
