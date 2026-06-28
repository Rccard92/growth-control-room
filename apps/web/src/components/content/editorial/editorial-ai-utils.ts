import type {
  ContentSeoEditorialItem,
  EditorialAiGenerationInfo,
  EditorialAiGenerationSnapshot,
} from "@gcr/shared";

export function formatAiCost(value: number | null | undefined): string {
  if (value === null || value === undefined) return "Costo non disponibile";
  return `$${value.toFixed(3)}`;
}

export function formatAiDate(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("it-IT", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function snapshotFromPayload(
  snapshot: EditorialAiGenerationSnapshot | undefined | null,
): EditorialAiGenerationInfo | null {
  if (!snapshot) return null;
  return {
    generated: snapshot.status === "success" || Boolean(snapshot.generatedAt),
    model: snapshot.model ?? null,
    modelTier: snapshot.modelTier ?? null,
    operationKey: snapshot.operationKey ?? null,
    contextProfile: snapshot.contextProfile ?? null,
    estimatedTotalCost: snapshot.estimatedTotalCost ?? null,
    inputTokens: snapshot.inputTokens ?? null,
    outputTokens: snapshot.outputTokens ?? null,
    createdAt: snapshot.generatedAt ?? null,
    status: snapshot.status ?? null,
    generatorVersion: snapshot.generatorVersion ?? null,
    logId: snapshot.logId ?? null,
    contextHash: snapshot.contextHash ?? null,
    promptHash: snapshot.promptHash ?? null,
  };
}

export function pickAiInfo(
  remote: EditorialAiGenerationInfo | null | undefined,
  fallback: EditorialAiGenerationInfo | null,
): EditorialAiGenerationInfo | null {
  return remote ?? fallback;
}

export function briefSnapshotFromItem(
  item: ContentSeoEditorialItem,
): EditorialAiGenerationInfo | null {
  const raw = item.briefPayload as { aiGeneration?: EditorialAiGenerationSnapshot } | null;
  return snapshotFromPayload(raw?.aiGeneration);
}

export function articleSnapshotFromItem(
  item: ContentSeoEditorialItem,
): EditorialAiGenerationInfo | null {
  return snapshotFromPayload(item.articlePayload?.aiGeneration);
}
