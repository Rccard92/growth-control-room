import type { SeoFormValues } from "./seoFormValues";
import type { SeoProductMetafieldItem } from "@gcr/shared";
import { toProposalValues } from "./seoFormValues";

export type FieldSource = "original" | "manual" | "ai";

export interface FieldState {
  value: string;
  originalValue: string;
  source: FieldSource;
  dirty: boolean;
  accepted: boolean;
  reasoning?: string;
  riskLevel?: string;
  generating?: boolean;
}

export type FieldStateMap = Record<string, FieldState>;

export type SeoEditableField =
  | "title"
  | "handle"
  | "seoTitle"
  | "metaDescription"
  | "descriptionHtml"
  | "imageAlt";

const TEXT_FIELD_KEYS: SeoEditableField[] = [
  "title",
  "handle",
  "seoTitle",
  "metaDescription",
  "descriptionHtml",
];

export function imageAltFieldKey(imageId: string | number): string {
  return `imageAlt:${imageId}`;
}

export function metafieldFieldKey(metafieldId: string): string {
  return `metafield:${metafieldId}`;
}

export function parseMetafieldFieldKey(key: string): string | null {
  if (!key.startsWith("metafield:")) return null;
  return key.slice("metafield:".length);
}

export function parseImageAltFieldKey(key: string): string | null {
  if (!key.startsWith("imageAlt:")) return null;
  return key.slice("imageAlt:".length);
}

function emptyFieldState(value = ""): FieldState {
  return {
    value,
    originalValue: value,
    source: "original",
    dirty: false,
    accepted: true,
  };
}

function fieldValueFromForm(
  key: string,
  formValues: SeoFormValues,
  mediaImages: Record<string, unknown>[],
  metafieldValues?: Record<string, string>,
): string {
  const metafieldId = parseMetafieldFieldKey(key);
  if (metafieldId && metafieldValues) {
    return metafieldValues[metafieldId] ?? "";
  }
  if (key === "imageAlt") {
    return String(formValues.imageAlt ?? "");
  }
  const imageId = parseImageAltFieldKey(key);
  if (imageId) {
    const img = mediaImages.find((m) => String(m.id ?? "") === imageId);
    return String(img?.altText ?? img?.alt ?? "");
  }
  return String(formValues[key] ?? "");
}

export function initFieldStateMap(
  formValues: SeoFormValues,
  entityType: "product" | "collection",
  mediaImages: Record<string, unknown>[] = [],
  metafields: SeoProductMetafieldItem[] = [],
  metafieldValues: Record<string, string> = {},
): FieldStateMap {
  const map: FieldStateMap = {};
  for (const key of TEXT_FIELD_KEYS) {
    const value = fieldValueFromForm(key, formValues, mediaImages, metafieldValues);
    map[key] = emptyFieldState(value);
  }
  if (entityType === "collection") {
    const alt = fieldValueFromForm("imageAlt", formValues, mediaImages, metafieldValues);
    map.imageAlt = emptyFieldState(alt);
  } else {
    for (const img of mediaImages) {
      const id = String(img.id ?? "");
      if (!id) continue;
      const fk = imageAltFieldKey(id);
      map[fk] = emptyFieldState(String(img.altText ?? img.alt ?? ""));
    }
    for (const mf of metafields) {
      const fk = metafieldFieldKey(mf.id);
      const val = metafieldValues[mf.id] ?? mf.value ?? "";
      map[fk] = emptyFieldState(val);
    }
  }
  return map;
}

export function syncFieldStateValues(
  map: FieldStateMap,
  formValues: SeoFormValues,
  mediaImages: Record<string, unknown>[],
): FieldStateMap {
  const next = { ...map };
  for (const key of Object.keys(next)) {
    const value = fieldValueFromForm(key, formValues, mediaImages);
    const row = next[key];
    if (!row) continue;
    next[key] = {
      ...row,
      value,
      dirty: value !== row.originalValue,
    };
  }
  return next;
}

export function updateFieldStateValue(
  map: FieldStateMap,
  key: string,
  value: string,
  source: FieldSource,
): FieldStateMap {
  const prev = map[key] ?? emptyFieldState();
  return {
    ...map,
    [key]: {
      ...prev,
      value,
      source: source === "original" ? "original" : source,
      dirty: value !== prev.originalValue,
      accepted: source === "manual",
      generating: false,
    },
  };
}

export function setFieldGenerating(map: FieldStateMap, key: string): FieldStateMap {
  const prev = map[key] ?? emptyFieldState();
  return {
    ...map,
    [key]: { ...prev, generating: true },
  };
}

export function applyAiFieldState(
  map: FieldStateMap,
  key: string,
  value: string,
  reasoning?: string,
  riskLevel?: string,
): FieldStateMap {
  const prev = map[key] ?? emptyFieldState();
  return {
    ...map,
    [key]: {
      ...prev,
      value,
      source: "ai",
      dirty: value !== prev.originalValue,
      accepted: false,
      reasoning,
      riskLevel,
      generating: false,
    },
  };
}

export function restoreFieldOriginal(map: FieldStateMap, key: string): FieldStateMap {
  const prev = map[key];
  if (!prev) return map;
  return {
    ...map,
    [key]: {
      ...prev,
      value: prev.originalValue,
      source: "original",
      dirty: false,
      accepted: true,
      reasoning: undefined,
      riskLevel: undefined,
      generating: false,
    },
  };
}

export function acceptFieldState(map: FieldStateMap, key: string): FieldStateMap {
  const prev = map[key];
  if (!prev) return map;
  return {
    ...map,
    [key]: {
      ...prev,
      accepted: true,
      reasoning: undefined,
    },
  };
}

export function markFieldsFromGlobalAi(
  map: FieldStateMap,
  changedKeys: string[],
  reasoning?: string,
  riskLevel?: string,
): FieldStateMap {
  let next = { ...map };
  for (const key of changedKeys) {
    const prev = next[key];
    if (!prev || !prev.dirty) continue;
    next[key] = {
      ...prev,
      source: "ai",
      accepted: false,
      reasoning,
      riskLevel,
    };
  }
  return next;
}

export function isApplicableField(row: FieldState): boolean {
  if (!row.dirty || row.value === row.originalValue) return false;
  return row.accepted || row.source === "manual";
}

export function getApplicableFieldKeys(map: FieldStateMap): string[] {
  return Object.entries(map)
    .filter(([, row]) => isApplicableField(row))
    .map(([key]) => key);
}

export function getChangedFieldKeys(map: FieldStateMap): string[] {
  return getApplicableFieldKeys(map);
}

export function hasApplicableChanges(map: FieldStateMap): boolean {
  return getApplicableFieldKeys(map).length > 0;
}

export function hasSaveableChanges(map: FieldStateMap): boolean {
  return hasApplicableChanges(map);
}

const API_FIELD_LABELS: Record<string, string> = {
  title: "Titolo",
  handle: "Handle URL",
  seoTitle: "SEO title",
  metaDescription: "Meta description",
  descriptionHtml: "Descrizione",
  imageAlt: "Alt immagine",
  imageAlts: "Alt immagini",
  metafields: "Metafield",
};

export function fieldLabelForKey(key: string): string {
  if (key.startsWith("imageAlt:")) return "Alt immagine";
  if (key.startsWith("metafield:")) return "Metafield";
  return API_FIELD_LABELS[key] ?? key;
}

export function toApiChangedFields(
  keys: string[],
  entityType: "product" | "collection",
): string[] {
  const apiFields = new Set<string>();
  for (const key of keys) {
    if (key.startsWith("imageAlt:")) {
      apiFields.add(entityType === "product" ? "imageAlts" : "imageAlt");
      continue;
    }
    if (key.startsWith("metafield:")) {
      apiFields.add("metafields");
      continue;
    }
    if (TEXT_FIELD_KEYS.includes(key as SeoEditableField) || key === "imageAlt") {
      apiFields.add(key);
    }
  }
  return Array.from(apiFields);
}

export function buildApplyFieldsPayload(
  formValues: SeoFormValues,
  entityType: "product" | "collection",
  mediaImages: Record<string, unknown>[],
  fieldStateMap: FieldStateMap,
  metafields: SeoProductMetafieldItem[] = [],
  metafieldValues: Record<string, string> = {},
): { fields: Record<string, unknown>; changedFields: string[] } {
  const applicableKeys = getApplicableFieldKeys(fieldStateMap);
  const { proposedValues } = buildChangedProposalValues(
    formValues,
    entityType,
    mediaImages,
    fieldStateMap,
    metafields,
  );

  const fields: Record<string, unknown> = {
    title: formValues.title,
    handle: formValues.handle,
    seoTitle: formValues.seoTitle,
    metaDescription: formValues.metaDescription,
    descriptionHtml: formValues.descriptionHtml,
  };

  if (entityType === "collection") {
    fields.imageAlt = formValues.imageAlt;
  } else {
    const changedImageIds = applicableKeys
      .filter((k) => k.startsWith("imageAlt:"))
      .map((k) => parseImageAltFieldKey(k))
      .filter((id): id is string => Boolean(id));
    if (changedImageIds.length > 0) {
      fields.imageAlts = (proposedValues.image_alts as Record<string, unknown>[]) ?? [];
      fields.mediaImages = mediaImages;
    }
    const changedMetafieldIds = applicableKeys
      .filter((k) => k.startsWith("metafield:"))
      .map((k) => parseMetafieldFieldKey(k))
      .filter((id): id is string => Boolean(id));
    if (changedMetafieldIds.length > 0 && proposedValues.metafields) {
      fields.metafields = proposedValues.metafields;
    }
    void metafieldValues;
  }

  return {
    fields,
    changedFields: toApiChangedFields(applicableKeys, entityType),
  };
}

export function formatApplicableFieldLabels(
  keys: string[],
  entityType: "product" | "collection",
): string[] {
  const apiFields = toApiChangedFields(keys, entityType);
  return apiFields.map((f) => API_FIELD_LABELS[f] ?? f);
}

export function commitFieldStateAsOriginal(map: FieldStateMap): FieldStateMap {
  const next: FieldStateMap = {};
  for (const [key, row] of Object.entries(map)) {
    next[key] = {
      ...row,
      originalValue: row.value,
      dirty: false,
      accepted: true,
      source: "original",
      reasoning: undefined,
      riskLevel: undefined,
      generating: false,
    };
  }
  return next;
}

export function formValuesFromFieldState(
  formValues: SeoFormValues,
  map: FieldStateMap,
  mediaImages: Record<string, unknown>[],
  entityType: "product" | "collection",
): { formValues: SeoFormValues; mediaImages: Record<string, unknown>[] } {
  const nextForm = { ...formValues };
  let nextMedia = [...mediaImages];

  for (const key of TEXT_FIELD_KEYS) {
    if (map[key]) nextForm[key] = map[key].value;
  }

  if (entityType === "collection" && map.imageAlt) {
    nextForm.imageAlt = map.imageAlt.value;
  }

  nextMedia = nextMedia.map((img) => {
    const id = String(img.id ?? "");
    const fk = imageAltFieldKey(id);
    if (!map[fk]) return img;
    return { ...img, altText: map[fk].value };
  });
  nextForm.images = nextMedia;

  return { formValues: nextForm, mediaImages: nextMedia };
}

export function buildChangedProposalValues(
  formValues: SeoFormValues,
  entityType: "product" | "collection",
  mediaImages: Record<string, unknown>[],
  fieldStateMap: FieldStateMap,
  metafields: SeoProductMetafieldItem[] = [],
): { proposedValues: Record<string, unknown>; changedFields: string[] } {
  const full = toProposalValues(formValues, entityType, mediaImages);
  const changedKeys = getChangedFieldKeys(fieldStateMap);
  const proposedValues: Record<string, unknown> = {};
  const changedFields: string[] = [];

  const snakeMap: Record<string, string> = {
    title: entityType === "product" ? "product_title" : "collection_title",
    handle: "handle",
    seoTitle: "seo_title",
    metaDescription: "meta_description",
    descriptionHtml: "description_html",
    imageAlt: entityType === "product" ? "image_alts" : "image_alt",
  };

  for (const key of changedKeys) {
    if (key.startsWith("imageAlt:")) {
      if (entityType === "product" && full.image_alts) {
        const imageId = parseImageAltFieldKey(key);
        const entry = (full.image_alts as Record<string, unknown>[]).find(
          (e) => String(e.image_id) === imageId,
        );
        if (entry) {
          if (!proposedValues.image_alts) {
            proposedValues.image_alts = [];
          }
          (proposedValues.image_alts as Record<string, unknown>[]).push(entry);
          if (!changedFields.includes("image_alts")) changedFields.push("image_alts");
          if (full.media_images) {
            proposedValues.media_images = full.media_images;
            if (!changedFields.includes("media_images")) changedFields.push("media_images");
          }
        }
      }
      continue;
    }
    if (key.startsWith("metafield:")) {
      if (entityType !== "product") continue;
      const metafieldId = parseMetafieldFieldKey(key);
      if (!metafieldId) continue;
      const mf = metafields.find((m) => m.id === metafieldId);
      const row = fieldStateMap[key];
      if (!mf || !row) continue;
      if (!proposedValues.metafields) {
        proposedValues.metafields = [];
      }
      (proposedValues.metafields as Record<string, unknown>[]).push({
        id: mf.id,
        namespace: mf.namespace,
        key: mf.key,
        type: mf.type,
        value: row.value,
      });
      if (!changedFields.includes("metafields")) changedFields.push("metafields");
      continue;
    }
    const snake = snakeMap[key];
    if (snake && full[snake] !== undefined) {
      proposedValues[snake] = full[snake];
      changedFields.push(snake);
    }
  }

  return { proposedValues, changedFields };
}

export function applyFieldValueToForm(
  formValues: SeoFormValues,
  mediaImages: Record<string, unknown>[],
  field: string,
  value: unknown,
  entityType: "product" | "collection",
): { formValues: SeoFormValues; mediaImages: Record<string, unknown>[] } {
  const nextForm = { ...formValues };
  let nextMedia = [...mediaImages];

  if (field === "imageAlt" && entityType === "collection") {
    nextForm.imageAlt = String(value ?? "");
    return { formValues: nextForm, mediaImages: nextMedia };
  }

  if (field === "imageAlt" && entityType === "product" && typeof value === "object" && value) {
    const row = value as Record<string, unknown>;
    const imageId = String(row.image_id ?? row.imageId ?? "");
    const alt = String(row.proposed_alt ?? row.proposedAlt ?? row.alt ?? "");
    nextMedia = nextMedia.map((img) =>
      String(img.id ?? "") === imageId ? { ...img, altText: alt } : img,
    );
    nextForm.images = nextMedia;
    return { formValues: nextForm, mediaImages: nextMedia };
  }

  const formKey = field as SeoEditableField;
  if (TEXT_FIELD_KEYS.includes(formKey)) {
    nextForm[formKey] = String(value ?? "");
  }

  return { formValues: nextForm, mediaImages: nextMedia };
}

export function applyMetafieldValue(
  metafieldValues: Record<string, string>,
  metafieldId: string,
  value: unknown,
): Record<string, string> {
  return { ...metafieldValues, [metafieldId]: String(value ?? "") };
}

export function applyGlobalMergeToFieldState(
  map: FieldStateMap,
  mergedForm: SeoFormValues,
  mediaImages: Record<string, unknown>[],
  changedKeys: string[],
): FieldStateMap {
  let next = { ...map };
  for (const key of changedKeys) {
    let value = "";
    if (key.startsWith("imageAlt:")) {
      const imageId = key.slice("imageAlt:".length);
      const img = mediaImages.find((m) => String(m.id ?? "") === imageId);
      value = String(img?.altText ?? img?.alt ?? "");
    } else {
      value = String(mergedForm[key] ?? "");
    }
    const prev = next[key] ?? emptyFieldState();
    next[key] = {
      ...prev,
      value,
      dirty: value !== prev.originalValue,
    };
  }
  return next;
}

export function collectChangedKeysFromMerge(
  before: SeoFormValues,
  after: SeoFormValues,
  entityType: "product" | "collection",
  mediaBefore: Record<string, unknown>[],
  mediaAfter: Record<string, unknown>[],
): string[] {
  const keys: string[] = [];
  for (const key of TEXT_FIELD_KEYS) {
    if (String(before[key] ?? "") !== String(after[key] ?? "")) keys.push(key);
  }
  if (entityType === "collection") {
    if (String(before.imageAlt ?? "") !== String(after.imageAlt ?? "")) keys.push("imageAlt");
  } else {
    mediaAfter.forEach((img, i) => {
      const id = String(img.id ?? i);
      const prevAlt = String(mediaBefore[i]?.altText ?? mediaBefore[i]?.alt ?? "");
      const nextAlt = String(img.altText ?? img.alt ?? "");
      if (prevAlt !== nextAlt) keys.push(imageAltFieldKey(id));
    });
  }
  return keys;
}
