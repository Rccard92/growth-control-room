export type AltBatchItemStatus = "pending" | "generated" | "skipped" | "failed";

export interface AltBatchItem {
  fieldKey: string;
  imageId: string;
  status: AltBatchItemStatus;
  reason?: string;
}

export interface AltBatchSummary {
  generated: number;
  skipped: number;
  failed: number;
  message: string;
}

export function isShopifyApplicableImage(img: Record<string, unknown>): boolean {
  if (img.shopifyApplicable === false) return false;
  const id = String(img.id ?? "").trim();
  if (!id) return false;
  return (
    id.startsWith("gid://shopify/MediaImage/")
    || id.startsWith("gid://shopify/ProductImage/")
    || id.startsWith("gid://shopify/ImageSource/")
  );
}

export function imageAltSkipReason(img: Record<string, unknown>): string | null {
  if (isShopifyApplicableImage(img)) return null;
  const reason = String(img.applicabilityReason ?? "").trim();
  if (reason === "missing_shopify_id") {
    return "Immagine senza riferimento Shopify";
  }
  if (reason === "missing_url") {
    return "URL immagine mancante";
  }
  if (reason === "invalid_shopify_id") {
    return "Campo non aggiornabile su Shopify";
  }
  if (!String(img.id ?? "").trim()) {
    return "Immagine senza riferimento Shopify";
  }
  return "Campo non aggiornabile su Shopify";
}

export function resolveImageAltFieldKey(
  img: Record<string, unknown>,
  index: number,
): { fieldKey: string; imageId: string; applicable: boolean } {
  const imageId = String(img.id ?? "").trim();
  if (imageId) {
    return {
      fieldKey: `imageAlt:${imageId}`,
      imageId,
      applicable: isShopifyApplicableImage(img),
    };
  }
  return {
    fieldKey: `imageAlt:local:${index}`,
    imageId: "",
    applicable: false,
  };
}

export function planMissingAltBatch(
  mediaImages: Record<string, unknown>[],
): { enqueue: AltBatchItem[]; skipped: AltBatchItem[] } {
  const enqueue: AltBatchItem[] = [];
  const skipped: AltBatchItem[] = [];
  const seen = new Set<string>();

  mediaImages.forEach((img, index) => {
    const alt = String(img.altText ?? img.alt ?? "").trim();
    if (alt) return;
    const { fieldKey, imageId, applicable } = resolveImageAltFieldKey(img, index);
    if (seen.has(fieldKey)) return;
    seen.add(fieldKey);
    if (!applicable) {
      skipped.push({
        fieldKey,
        imageId,
        status: "skipped",
        reason: imageAltSkipReason(img) ?? "Campo non aggiornabile su Shopify",
      });
      return;
    }
    enqueue.push({ fieldKey, imageId, status: "pending" });
  });

  return { enqueue, skipped };
}

export function formatAltBatchSummary(
  generated: number,
  skipped: number,
  failed: number,
): AltBatchSummary {
  const parts: string[] = [];
  if (generated > 0) parts.push(`${generated} ALT generat${generated === 1 ? "o" : "i"}`);
  if (skipped > 0) parts.push(`${skipped} saltat${skipped === 1 ? "o" : "i"}`);
  if (failed > 0) parts.push(`${failed} fallit${failed === 1 ? "o" : "i"}`);
  return {
    generated,
    skipped,
    failed,
    message: parts.length > 0 ? `${parts.join(", ")}.` : "Nessuna immagine da elaborare.",
  };
}

export function applicabilityNote(img: Record<string, unknown>): string | undefined {
  const skip = imageAltSkipReason(img);
  if (!skip) return undefined;
  const alt = String(img.altText ?? img.alt ?? "").trim();
  if (alt) {
    return "Bozza locale — immagine non aggiornabile su Shopify";
  }
  return skip;
}
