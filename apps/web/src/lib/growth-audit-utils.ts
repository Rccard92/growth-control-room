import type { GrowthAuditPageType, GrowthAuditRunStatus } from "@gcr/shared";

const STATUS_LABELS: Record<string, string> = {
  pending: "In attesa",
  queued: "In coda",
  discovering: "Discovery in corso",
  classifying: "Classificazione",
  analyzing: "Analisi in corso",
  ready_for_analysis: "Pronto per analisi",
  completed: "Completato",
  failed: "Fallito",
  partial_failed: "Parzialmente fallito",
  cancelled: "Annullato",
};

const PHASE_LABELS: Record<string, string> = {
  queued: "In coda",
  discovery: "Discovery",
  classification: "Classificazione",
  analysis: "Analisi",
  ready_for_analysis: "Pronto per analisi",
  completed: "Completato",
  failed: "Fallito",
};

const PAGE_TYPE_LABELS: Record<string, string> = {
  homepage: "Homepage",
  product: "Prodotto",
  collection: "Collezione",
  blog: "Blog",
  article: "Articolo",
  page: "Pagina",
  policy: "Policy",
  cart: "Carrello",
  checkout: "Checkout",
  search: "Ricerca",
  account: "Account",
  other: "Altro",
  unknown: "Sconosciuto",
};

const PAGE_STATUS_LABELS: Record<string, string> = {
  pending: "In attesa",
  discovered: "Scoperta",
  classified: "Classificata",
  analyzed: "Analizzata",
  failed: "Fallita",
  skipped: "Saltata",
};

const PAGE_SOURCE_LABELS: Record<string, string> = {
  seed: "Seed",
  sitemap: "Sitemap",
  crawl: "Crawl",
  manual: "Manuale",
};

export function getGrowthAuditStatusLabel(status?: GrowthAuditRunStatus | string | null): string {
  if (!status) return "—";
  return STATUS_LABELS[status] ?? status;
}

export function getGrowthAuditPhaseLabel(phase?: string | null): string {
  if (!phase) return "—";
  return PHASE_LABELS[phase] ?? phase;
}

export function getGrowthAuditPageTypeLabel(pageType?: GrowthAuditPageType | string | null): string {
  if (!pageType) return "—";
  return PAGE_TYPE_LABELS[pageType] ?? pageType;
}

export function getGrowthAuditPageStatusLabel(status?: string | null): string {
  if (!status) return "—";
  return PAGE_STATUS_LABELS[status] ?? status;
}

export function getGrowthAuditPageSourceLabel(source?: string | null): string {
  if (!source) return "—";
  return PAGE_SOURCE_LABELS[source] ?? source;
}

export function isGrowthAuditRunActive(status?: GrowthAuditRunStatus | string | null): boolean {
  return Boolean(
    status &&
      ["pending", "queued", "discovering", "classifying", "analyzing", "ready_for_analysis"].includes(
        status,
      ),
  );
}

export function getDefaultRootUrl(shopDomain?: string | null): string {
  if (!shopDomain) return "";
  const trimmed = shopDomain.trim();
  if (!trimmed) return "";
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    return trimmed;
  }
  return `https://${trimmed}`;
}
