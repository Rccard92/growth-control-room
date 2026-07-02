import type { SeoSkillCatalogItem, SeoSkillRunResult, SeoSkillRunStatus } from "@gcr/shared";

export const SEO_SKILL_CATEGORY_FILTERS = [
  { key: "all", label: "Tutte" },
  { key: "audit", label: "Audit" },
  { key: "content", label: "Content" },
  { key: "schema", label: "Schema" },
  { key: "ai_search", label: "AI Search" },
  { key: "ecommerce", label: "Ecommerce" },
  { key: "images", label: "Images" },
  { key: "local", label: "Local" },
  { key: "monitoring", label: "Monitoring" },
  { key: "external_data", label: "External Data" },
] as const;

export type SeoSkillCategoryFilterKey = (typeof SEO_SKILL_CATEGORY_FILTERS)[number]["key"];

const CATEGORY_LABELS: Record<string, string> = {
  audit: "Audit",
  content: "Content",
  structured_data: "Schema",
  schema: "Schema",
  ai_search: "AI Search",
  ecommerce: "Ecommerce",
  media: "Images",
  images: "Images",
  local: "Local",
  monitoring: "Monitoring",
  integrations: "External Data",
  external_data: "External Data",
  sitemap: "Sitemap",
  strategy: "Strategy",
  competitive: "Competitive",
};

const FILTER_CATEGORY_ALIASES: Record<string, string[]> = {
  schema: ["structured_data", "schema"],
  images: ["media", "images"],
  external_data: ["integrations", "external_data"],
};

const STATUS_LABELS: Record<string, string> = {
  available: "Disponibile",
  needs_config: "Configurazione richiesta",
  external_required: "Integrazione esterna",
  planned: "In roadmap",
};

const RUNTIME_LABELS: Record<string, string> = {
  prompt_only: "Analisi AI",
  connector_required: "Connector richiesto",
  external_api_required: "API esterna richiesta",
  planned: "Pianificato",
};

const RUN_STATUS_LABELS: Record<string, string> = {
  pending: "In attesa",
  running: "Analisi in corso",
  completed: "Completata",
  partial_failed: "Completata con errori",
  failed: "Fallita",
};

export interface SeoSkillRunResultsSummary {
  selectedCount: number;
  completedCount: number;
  failedCount: number;
  firstFailure?: {
    label: string;
    errorMessage: string;
  };
}

export interface SeoSkillFindingView {
  severity: string;
  severityLabel: string;
  priority: string;
  priorityLabel: string;
  area: string;
  title: string;
  description: string;
  evidence: string;
  recommendation: string;
  howToValidate: string;
}

export interface SeoSkillRecommendationView {
  title: string;
  description: string;
  priority: string;
  priorityLabel: string;
  impact: string;
  impactLabel: string;
  effort: string;
  effortLabel: string;
}

export interface SeoSkillTaskView {
  title: string;
  description: string;
  priority: string;
  priorityLabel: string;
  ownerType: string;
  ownerTypeLabel: string;
  estimatedEffort: string;
  estimatedEffortLabel: string;
}

export interface SeoSkillArtifactsView {
  jsonLd: unknown[];
  markdownReport: string;
  shopifySidekickPrompts: string[];
  implementationNotes: string[];
}

export interface SeoSkillRunPanelSummary {
  total: number;
  completed: number;
  failed: number;
  running: number;
  pending: number;
}

const RESULT_STATUS_LABELS: Record<string, string> = {
  pending: "In attesa",
  running: "In corso",
  completed: "Completata",
  failed: "Fallita",
};

const SEVERITY_LABELS: Record<string, string> = {
  critical: "Critico",
  high: "Alta",
  medium: "Media",
  low: "Bassa",
  info: "Info",
};

const PRIORITY_LABELS: Record<string, string> = {
  high: "Alta",
  medium: "Media",
  low: "Bassa",
};

const OWNER_TYPE_LABELS: Record<string, string> = {
  content: "Contenuto",
  dev: "Sviluppo",
  seo: "SEO",
  design: "Design",
  ads: "Ads",
};

const EFFORT_LABELS: Record<string, string> = {
  low: "Basso",
  medium: "Medio",
  high: "Alto",
};

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

const MAX_DISPLAY_TEXT = 1200;

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asString(value: unknown): string {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

function truncateText(value: string, maxLength = MAX_DISPLAY_TEXT): string {
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength)}…`;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => asString(item)).filter(Boolean);
}

function asUnknownArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function labelFromMap(value: string, map: Record<string, string>): string {
  const normalized = value.trim().toLowerCase();
  return map[normalized] ?? formatSkillCategory(normalized || value);
}

export function formatSeoSkillResultStatus(status?: string | null): string {
  if (!status) return "";
  return RESULT_STATUS_LABELS[status] ?? formatSkillCategory(status);
}

export function getSeverityLabel(severity: string): string {
  return labelFromMap(severity, SEVERITY_LABELS);
}

export function getPriorityLabel(priority: string): string {
  return labelFromMap(priority, PRIORITY_LABELS);
}

export function getOwnerTypeLabel(ownerType: string): string {
  return labelFromMap(ownerType, OWNER_TYPE_LABELS);
}

export function getEffortLabel(effort: string): string {
  return labelFromMap(effort, EFFORT_LABELS);
}

export function getSkillDisplayName(
  skillKey: string,
  catalogSkills?: Map<string, SeoSkillCatalogItem> | SeoSkillCatalogItem[],
): string {
  const map =
    catalogSkills instanceof Map
      ? catalogSkills
      : new Map((catalogSkills ?? []).map((skill) => [skill.key, skill]));
  return map.get(skillKey)?.label ?? skillKey;
}

function getRawOutputRecord(result: SeoSkillRunResult): Record<string, unknown> {
  return asRecord(result.rawOutput);
}

export function getResultSummary(result: SeoSkillRunResult): string {
  const raw = getRawOutputRecord(result);
  const nested = asRecord(raw.rawOutput);
  const candidates = [asString(raw.summary), asString(nested.summary)];
  for (const candidate of candidates) {
    if (candidate) return truncateText(candidate);
  }
  return "";
}

export function getResultScore(result: SeoSkillRunResult): number | null {
  if (typeof result.score === "number" && Number.isFinite(result.score)) {
    return Math.round(result.score);
  }
  const raw = getRawOutputRecord(result);
  const nested = asRecord(raw.rawOutput);
  const candidates = [raw.score, nested.score];
  for (const candidate of candidates) {
    if (typeof candidate === "number" && Number.isFinite(candidate)) {
      return Math.round(candidate);
    }
  }
  return null;
}

export function normalizeFindings(value: unknown): SeoSkillFindingView[] {
  const items = asUnknownArray(value);
  const normalized: SeoSkillFindingView[] = [];

  for (const item of items) {
    const data = asRecord(item);
    const title = asString(data.title);
    const description = asString(data.description);
    if (!title && !description) continue;

    const severity = asString(data.severity) || "info";
    const priority = asString(data.priority) || "medium";
    normalized.push({
      severity,
      severityLabel: getSeverityLabel(severity),
      priority,
      priorityLabel: getPriorityLabel(priority),
      area: truncateText(asString(data.area), 120),
      title: truncateText(title, 200),
      description: truncateText(description),
      evidence: truncateText(asString(data.evidence)),
      recommendation: truncateText(asString(data.recommendation)),
      howToValidate: truncateText(asString(data.howToValidate)),
    });
  }

  return normalized.sort((left, right) => {
    const leftOrder = SEVERITY_ORDER[left.severity] ?? 99;
    const rightOrder = SEVERITY_ORDER[right.severity] ?? 99;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    return left.title.localeCompare(right.title);
  });
}

export function normalizeRecommendations(value: unknown): SeoSkillRecommendationView[] {
  const items = asUnknownArray(value);
  const normalized: SeoSkillRecommendationView[] = [];

  for (const item of items) {
    const data = asRecord(item);
    const title = asString(data.title);
    const description = asString(data.description);
    if (!title && !description) continue;

    const priority = asString(data.priority) || "medium";
    const impact = asString(data.impact) || "medium";
    const effort = asString(data.effort) || "medium";
    normalized.push({
      title: truncateText(title, 200),
      description: truncateText(description),
      priority,
      priorityLabel: getPriorityLabel(priority),
      impact,
      impactLabel: getPriorityLabel(impact),
      effort,
      effortLabel: getEffortLabel(effort),
    });
  }

  return normalized;
}

export function normalizeTasks(value: unknown): SeoSkillTaskView[] {
  const items = asUnknownArray(value);
  const normalized: SeoSkillTaskView[] = [];

  for (const item of items) {
    const data = asRecord(item);
    const title = asString(data.title);
    const description = asString(data.description);
    if (!title && !description) continue;

    const priority = asString(data.priority) || "medium";
    const ownerType = asString(data.ownerType) || "seo";
    const estimatedEffort = asString(data.estimatedEffort) || "medium";
    normalized.push({
      title: truncateText(title, 200),
      description: truncateText(description),
      priority,
      priorityLabel: getPriorityLabel(priority),
      ownerType,
      ownerTypeLabel: getOwnerTypeLabel(ownerType),
      estimatedEffort,
      estimatedEffortLabel: getEffortLabel(estimatedEffort),
    });
  }

  return normalized;
}

export function normalizeArtifacts(value: unknown): SeoSkillArtifactsView {
  const data = asRecord(value);
  return {
    jsonLd: asUnknownArray(data.jsonLd),
    markdownReport: truncateText(asString(data.markdownReport), 2000),
    shopifySidekickPrompts: asStringArray(data.shopifySidekickPrompts).map((item) =>
      truncateText(item, 1000),
    ),
    implementationNotes: asStringArray(data.implementationNotes).map((item) =>
      truncateText(item, 1000),
    ),
  };
}

export function getResultFindings(result: SeoSkillRunResult): SeoSkillFindingView[] {
  if (result.findings?.length) {
    return normalizeFindings(result.findings);
  }
  const raw = getRawOutputRecord(result);
  return normalizeFindings(raw.findings);
}

export function getResultRecommendations(
  result: SeoSkillRunResult,
): SeoSkillRecommendationView[] {
  if (result.recommendations?.length) {
    return normalizeRecommendations(result.recommendations);
  }
  const raw = getRawOutputRecord(result);
  return normalizeRecommendations(raw.recommendations);
}

export function getResultTasks(result: SeoSkillRunResult): SeoSkillTaskView[] {
  if (result.tasks?.length) {
    return normalizeTasks(result.tasks);
  }
  const raw = getRawOutputRecord(result);
  return normalizeTasks(raw.tasks);
}

export function getResultArtifacts(result: SeoSkillRunResult): SeoSkillArtifactsView {
  if (result.artifacts) {
    return normalizeArtifacts(result.artifacts);
  }
  const raw = getRawOutputRecord(result);
  return normalizeArtifacts(raw.artifacts);
}

export function buildRunPanelSummary(
  results: SeoSkillRunResult[] | undefined,
): SeoSkillRunPanelSummary {
  const items = results ?? [];
  return {
    total: items.length,
    completed: items.filter((item) => item.status === "completed").length,
    failed: items.filter((item) => item.status === "failed").length,
    running: items.filter((item) => item.status === "running").length,
    pending: items.filter((item) => item.status === "pending").length,
  };
}

export function formatRunPanelHeadline(status?: SeoSkillRunStatus | string | null): string {
  if (!status) return "Risultati analisi";
  if (status === "pending" || status === "running") return "Analisi in corso";
  if (status === "completed") return "Analisi completata";
  if (status === "partial_failed") return "Analisi completata con errori";
  if (status === "failed") return "Analisi fallita";
  return "Risultati analisi";
}

export async function copyTextToClipboard(text: string): Promise<boolean> {
  if (!text.trim()) return false;
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    return false;
  }
  return false;
}

export function formatRunTimestamp(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("it-IT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function isSkillSelectable(skill: SeoSkillCatalogItem): boolean {
  return skill.enabled && skill.status === "available" && skill.runtime === "prompt_only";
}

export function getSkillDisabledReason(skill: SeoSkillCatalogItem): string | null {
  if (isSkillSelectable(skill)) return null;
  if (!skill.enabled) return "Skill disabilitata";
  if (skill.status === "needs_config") return "Richiede configurazione";
  if (skill.status === "external_required") return "Richiede integrazione esterna";
  if (skill.status === "planned") return "In roadmap";
  if (skill.runtime !== "prompt_only") return "Runtime non ancora supportato";
  return "Non disponibile";
}

export function formatSkillCategory(category: string): string {
  const normalized = category.trim().toLowerCase();
  if (CATEGORY_LABELS[normalized]) return CATEGORY_LABELS[normalized];
  return normalized
    .split(/[_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function formatSkillStatus(status: string): string {
  return STATUS_LABELS[status] ?? formatSkillCategory(status);
}

export function formatSkillRuntime(runtime: string): string {
  return RUNTIME_LABELS[runtime] ?? formatSkillCategory(runtime);
}

export function formatSeoSkillRunStatus(status?: SeoSkillRunStatus | string | null): string {
  if (!status) return "";
  return RUN_STATUS_LABELS[status] ?? formatSkillCategory(status);
}

export function formatDefaultProvider(provider: string): string {
  const normalized = provider.trim();
  if (!normalized) return "Provider predefinito: —";
  const label = normalized.charAt(0).toUpperCase() + normalized.slice(1);
  return `Provider predefinito: ${label}`;
}

export function buildRunResultsSummary(
  results: SeoSkillRunResult[] | undefined,
  skillsByKey: Map<string, SeoSkillCatalogItem>,
): SeoSkillRunResultsSummary | null {
  if (!results?.length) return null;

  const completedCount = results.filter((item) => item.status === "completed").length;
  const failedCount = results.filter((item) => item.status === "failed").length;
  const firstFailed = results.find((item) => item.status === "failed");

  const summary: SeoSkillRunResultsSummary = {
    selectedCount: results.length,
    completedCount,
    failedCount,
  };

  if (firstFailed) {
    const label = skillsByKey.get(firstFailed.skillKey)?.label ?? firstFailed.skillKey;
    summary.firstFailure = {
      label,
      errorMessage: firstFailed.errorMessage?.trim() || "Errore durante l'esecuzione della skill.",
    };
  }

  return summary;
}

export function matchesCategoryFilter(
  skill: SeoSkillCatalogItem,
  filterKey: SeoSkillCategoryFilterKey,
): boolean {
  if (filterKey === "all") return true;
  const category = skill.category.trim().toLowerCase();
  const aliases = FILTER_CATEGORY_ALIASES[filterKey] ?? [filterKey];
  return aliases.includes(category);
}

export function canSubmitLauncher(input: {
  selectedCount: number;
  targetUrl: string;
  isSubmitting: boolean;
}): boolean {
  if (input.isSubmitting) return false;
  if (input.selectedCount <= 0) return false;
  return input.targetUrl.trim().length > 0;
}

export function formatSeoSkillRunError(err: unknown): string {
  const raw = err instanceof Error ? err.message : "Errore durante l'avvio della run.";
  const lowered = raw.toLowerCase();

  if (lowered.includes("claude provider is not configured") || lowered.includes("claude non configurato")) {
    return "Provider Claude non configurato sul backend.";
  }
  if (lowered.includes("openai provider is not configured") || lowered.includes("openai non configurato")) {
    return "Provider OpenAI non configurato sul backend.";
  }
  if (lowered.includes("risposta vuota") || lowered.includes("risposta openai vuota")) {
    return "OpenAI ha restituito una risposta vuota. Riprova con un modello più stabile o con provider Claude.";
  }
  if (lowered.includes("json valido") || lowered.includes("non è json valido")) {
    return "OpenAI non ha restituito un JSON valido. Riprova l'analisi o usa un modello più stabile.";
  }
  if (
    lowered.includes("output_truncated") ||
    lowered.includes("interrotto la risposta") ||
    lowered.includes("troppo lungo")
  ) {
    return "OpenAI ha interrotto la risposta perché l'output era troppo lungo. Riprova l'analisi con meno skill o un modello con più token.";
  }
  if (lowered.includes("not available") || lowered.includes("non disponibile")) {
    return "Una o più skill selezionate non sono disponibili.";
  }
  if (lowered.includes("url") && (lowered.includes("required") || lowered.includes("richiest"))) {
    return "Inserisci una URL target valida.";
  }
  if (lowered.includes("422") || lowered.includes("validation")) {
    return raw.startsWith("Errore") ? raw : `Richiesta non valida: ${raw}`;
  }

  return raw || "Errore durante l'avvio della run.";
}
