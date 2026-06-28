import { describe, expect, it } from "vitest";
import {
  canApproveImage,
  DEFAULT_IMAGE_FINAL_SIZE,
  DEFAULT_IMAGE_PROVIDER_SIZE,
  formatImageCost,
  formatImageDimensions,
  formatImageFinalSize,
  formatImageProviderSize,
  getImageStatusLabel,
  getImageSyncLabel,
  hasApprovedImageForPublish,
  hasShopifyCdnUrl,
  IMAGE_POST_PROCESSING_LABEL,
  IMAGE_STALE_MESSAGE,
  isImageFilenameStale,
  isImageModified,
  isImageShopifySynced,
  parseEditorialImagePayload,
  SHOPIFY_SCOPE_MISSING_WARNING,
} from "./editorial-image-utils";

describe("editorial-image-utils", () => {
  it("formatta label stato immagine", () => {
    expect(getImageStatusLabel("approved")).toBe("Approvata");
    expect(getImageStatusLabel("generated")).toBe("Generata");
    expect(getImageStatusLabel("uploaded")).toBe("Caricata su Shopify");
    expect(getImageStatusLabel("upload_error")).toBe("Upload fallito");
    const modified = parseEditorialImagePayload({
      imageStatus: "generated",
      imageRevisionNote: "Più luce",
    });
    expect(getImageStatusLabel("generated", modified)).toContain("Modificata");
  });

  it("formatta costo immagine", () => {
    expect(formatImageCost(0.04)).toBe("$0.0400");
    expect(formatImageCost(null)).toBe("—");
  });

  it("parse payload camelCase con nuovi campi", () => {
    const parsed = parseEditorialImagePayload({
      imageStatus: "generated",
      imagePrompt: "A premium honey jar",
      imageAlt: "Guida al miele",
      imageFilename: "guida-al-miele.jpg",
      imageWidth: 1200,
      imageHeight: 800,
      imageProviderSize: "1536x1024",
      imageProviderReturnedSize: "1536x1024",
      imagePostProcessingApplied: "cover_crop_3_2 + resize_jpg",
      imageFinalSize: "1200x800",
      generatedFromArticleHash: "abc123",
      shopifyImageReady: false,
      accessToken: "abc",
    });
    expect(parsed.imageStatus).toBe("generated");
    expect(parsed.imagePrompt).toContain("honey");
    expect(parsed.imageFinalSize).toBe("1200x800");
    expect(parsed.imageProviderReturnedSize).toBe("1536x1024");
    expect(parsed.generatedFromArticleHash).toBe("abc123");
    expect(formatImageDimensions(parsed)).toBe("1200×800");
    expect(formatImageProviderSize(parsed)).toBe("1536×1024");
    expect(formatImageFinalSize(parsed)).toBe("1200×800");
  });

  it("usa default provider/final size quando assenti", () => {
    expect(formatImageProviderSize({ imageStatus: "not_generated" })).toBe(
      DEFAULT_IMAGE_PROVIDER_SIZE.replace("x", "×"),
    );
    expect(formatImageFinalSize({ imageStatus: "not_generated" })).toBe(
      DEFAULT_IMAGE_FINAL_SIZE.replace("x", "×"),
    );
    expect(DEFAULT_IMAGE_FINAL_SIZE).toBe("1200x800");
    expect(IMAGE_POST_PROCESSING_LABEL).toBe("crop 3:2 + resize");
  });

  it("rileva filename stale rispetto al titolo", () => {
    const image = parseEditorialImagePayload({
      imageStatus: "approved",
      imageFilename: "vecchio-titolo.jpg",
    });
    expect(isImageFilenameStale(image, "Nuovo titolo completamente diverso")).toBe(true);
  });

  it("hasApprovedImageForPublish con backup", () => {
    const image = parseEditorialImagePayload({
      imageStatus: "generated",
      approvedImageBackup: { imageUrl: "https://cdn.example.com/x.jpg" },
    });
    expect(hasApprovedImageForPublish(image)).toBe(true);
  });

  it("canApproveImage richiede URL CDN Shopify", () => {
    const uploaded = parseEditorialImagePayload({
      imageStatus: "uploaded",
      imageUrl: "https://cdn.shopify.com/s/files/1/hero.jpg",
      shopifyImageReady: true,
    });
    expect(canApproveImage(uploaded)).toBe(true);
    expect(hasShopifyCdnUrl(uploaded)).toBe(true);

    const uploadError = parseEditorialImagePayload({
      imageStatus: "upload_error",
      imageUploadError: "Timeout",
    });
    expect(canApproveImage(uploadError)).toBe(false);
  });

  it("sync label e modified state", () => {
    expect(isImageModified({ imageStatus: "generated", imageRevisionNote: "x" })).toBe(true);
    expect(
      isImageShopifySynced({
        imageStatus: "approved",
        imageApprovedAt: "2026-06-01T10:00:00Z",
        shopifyImageSyncedAt: "2026-06-01T11:00:00Z",
        shopifyImageReady: true,
      }),
    ).toBe(true);
    expect(
      getImageSyncLabel({
        imageStatus: "approved",
        shopifyImageReady: true,
        shopifyImageSyncedAt: "2026-06-01T11:00:00Z",
        imageApprovedAt: "2026-06-01T10:00:00Z",
      }),
    ).toBe("Sincronizzata con Shopify");
  });

  it("espone messaggi warning", () => {
    expect(IMAGE_STALE_MESSAGE).toContain("non essere aggiornata");
    expect(SHOPIFY_SCOPE_MISSING_WARNING).toContain("write_files");
  });
});
