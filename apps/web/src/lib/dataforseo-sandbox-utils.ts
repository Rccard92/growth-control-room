export const SEARCH_VOLUME_BATCH_MAX_KEYWORDS = 10;

export const SOLMIELATO_DEFAULT_KEYWORDS = [
  "polline biologico",
  "miele di eucalipto",
  "miele di acacia",
  "miele millefiori",
  "propoli biologica",
  "miele di castagno",
  "miele di tarassaco",
  "polline d'api",
  "miele biologico",
  "gelatina reale",
] as const;

const OBSERVED_SEARCH_VOLUME_SINGLE_COST_USD = 0.09;

export function parseKeywordBatch(text: string): string[] {
  const resolved: string[] = [];
  const seen = new Set<string>();

  for (const line of text.split(/\r?\n/)) {
    for (const part of line.split(",")) {
      const cleaned = part.trim();
      if (!cleaned) continue;
      const key = cleaned.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      resolved.push(cleaned);
    }
  }

  return resolved;
}

export function formatTrend(direction: string | null | undefined): string {
  switch (direction) {
    case "up":
      return "↑ In crescita";
    case "down":
      return "↓ In calo";
    case "stable":
      return "→ Stabile";
    case "unknown":
      return "— Sconosciuto";
    default:
      return "—";
  }
}

export function estimateBatchRunCostUsd(keywordCount: number): number {
  if (keywordCount <= 0) return 0;
  return Math.max(
    OBSERVED_SEARCH_VOLUME_SINGLE_COST_USD * keywordCount,
    OBSERVED_SEARCH_VOLUME_SINGLE_COST_USD,
  );
}

export function formatCostPerItem(
  costUsd: number | null | undefined,
  itemsCount: number | null | undefined,
): string {
  if (costUsd == null || !itemsCount || itemsCount <= 0) return "—";
  return `$${(costUsd / itemsCount).toFixed(4)}`;
}
