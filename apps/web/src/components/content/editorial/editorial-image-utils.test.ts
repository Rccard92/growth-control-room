import { describe, expect, it } from "vitest";
import {
  DEFAULT_IMAGE_FINAL_SIZE,
  DEFAULT_IMAGE_PROVIDER_SIZE,
  formatImageCost,
  formatImageDimensions,
  formatImageFinalSize,
  formatImageProviderSize,
  getImageStatusLabel,
  hasApprovedImageForPublish,
  IMAGE_POST_PROCESSING_LABEL,
  IMAGE_STALE_MESSAGE,
  isImageFilenameStale,
  parseEditorialImagePayload,
  PUBLIC_STORAGE_WARNING,
} from "./editorial-image-utils";

describe("editorial-image-utils", () => {
  it("formatta label stato immagine", () => {
    expect(getImageStatusLabel("approved")).toBe("Approvata");
    expect(getImageStatusLabel("generated")).toBe("Generata");
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
      imageWidth: 1600,
      imageHeight: 900,
      imageProviderSize: "1536x1024",
      imageFinalSize: "1600x900",
      shopifyImageReady: false,
      accessToken: "abc",
    });
    expect(parsed.imageStatus).toBe("generated");
    expect(parsed.imagePrompt).toContain("honey");
    expect(parsed.imageAlt).toBe("Guida al miele");
    expect(parsed.imageFilename).toBe("guida-al-miele.jpg");
    expect(parsed.imageProviderSize).toBe("1536x1024");
    expect(parsed.imageFinalSize).toBe("1600x900");
    expect(parsed.shopifyImageReady).toBe(false);
    expect(formatImageDimensions(parsed)).toBe("1600×900");
    expect(formatImageProviderSize(parsed)).toBe("1536×1024");
    expect(formatImageFinalSize(parsed)).toBe("1600×900");
  });

  it("usa default provider/final size quando assenti", () => {
    expect(formatImageProviderSize({ imageStatus: "not_generated" })).toBe(
      DEFAULT_IMAGE_PROVIDER_SIZE.replace("x", "×"),
    );
    expect(formatImageFinalSize({ imageStatus: "not_generated" })).toBe(
      DEFAULT_IMAGE_FINAL_SIZE.replace("x", "×"),
    );
    expect(IMAGE_POST_PROCESSING_LABEL).toBe("crop 16:9 + resize");
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

  it("espone messaggi warning", () => {
    expect(IMAGE_STALE_MESSAGE).toContain("non essere aggiornata");
    expect(PUBLIC_STORAGE_WARNING).toContain("Shopify");
  });
});
