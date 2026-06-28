import { describe, expect, it } from "vitest";
import {
  formatImageCost,
  formatImageDimensions,
  getImageStatusLabel,
  hasApprovedImageForPublish,
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
      shopifyImageReady: false,
      accessToken: "abc",
    });
    expect(parsed.imageStatus).toBe("generated");
    expect(parsed.imagePrompt).toContain("honey");
    expect(parsed.imageAlt).toBe("Guida al miele");
    expect(parsed.imageFilename).toBe("guida-al-miele.jpg");
    expect(parsed.shopifyImageReady).toBe(false);
    expect(formatImageDimensions(parsed)).toBe("1600×900");
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
