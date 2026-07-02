import type { SeoSkillCatalogItem } from "@gcr/shared";

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
  prompt_only: "Prompt only",
  connector_required: "Connector richiesto",
  external_api_required: "API esterna richiesta",
  planned: "Pianificato",
};

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
