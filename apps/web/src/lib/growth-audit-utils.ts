import type {
  GrowthAuditFinding,
  GrowthAuditInventoryCounts,
  GrowthAuditInventoryFilter,
  GrowthAuditPage,
  GrowthAuditPageAiMetadata,
  GrowthAuditPagePerformanceMetadata,
  GrowthAuditPageSearchConsoleMetadata,
  GrowthAuditPageResult,
  GrowthAuditPageStatusFilter,
  GrowthAuditPageType,
  GrowthAuditRunStatus,
  GrowthAuditRunSummary,
  GrowthAuditScoreFilter,
  GrowthAuditSourceEntityType,
  GrowthAuditTask,
} from "@gcr/shared";

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
  technical_scan: "Scansione tecnica",
  ready_for_analysis: "Pronto per analisi",
  finalization: "Finalizzazione",
  completed: "Completato",
  failed: "Fallito",
};

const PAGE_TYPE_LABELS: Record<string, string> = {
  homepage: "Homepage",
  product: "Prodotto",
  collection: "Collezione",
  blog: "Blog",
  blog_article: "Articolo blog",
  article: "Articolo",
  static_page: "Pagina statica",
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
  analyzing: "In analisi",
  analyzed: "Analizzata",
  failed: "Fallita",
  skipped: "Saltata",
};

const PAGE_SOURCE_LABELS: Record<string, string> = {
  seed: "Seed",
  sitemap: "Sitemap",
  shopify_product: "Shopify prodotto",
  shopify_collection: "Shopify collezione",
  shopify_page: "Shopify pagina",
  shopify_blog: "Shopify blog",
  crawl: "Crawl",
  manual: "Manuale",
};

const SOURCE_ENTITY_TYPE_LABELS: Record<string, string> = {
  shopify_product: "Prodotto Shopify",
  shopify_collection: "Collection Shopify",
  shopify_page: "Pagina Shopify",
  shopify_article: "Articolo Shopify",
};

const INVENTORY_FILTER_LABELS: Record<GrowthAuditInventoryFilter, string> = {
  all: "Tutte",
  homepage: "Homepage",
  product: "Prodotti",
  collection: "Categorie",
  blog: "Blog",
  static_page: "Statiche",
  unknown: "Sconosciute",
};

export const GROWTH_AUDIT_MAX_PAGES_OPTIONS = [25, 50, 100, 200] as const;

export const GROWTH_AUDIT_INVENTORY_FILTERS: GrowthAuditInventoryFilter[] = [
  "all",
  "homepage",
  "product",
  "collection",
  "blog",
  "static_page",
  "unknown",
];

export const GROWTH_AUDIT_SCORE_FILTERS: { value: GrowthAuditScoreFilter; label: string }[] = [
  { value: "all", label: "Tutte" },
  { value: "critical", label: "Critiche <60" },
  { value: "warning", label: "Da migliorare 60-79" },
  { value: "good", label: "Buone 80+" },
];

export const GROWTH_AUDIT_STATUS_FILTERS: { value: GrowthAuditPageStatusFilter; label: string }[] =
  [
    { value: "all", label: "Tutte" },
    { value: "analyzed", label: "Analizzate" },
    { value: "failed", label: "Fallite" },
  ];

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

const PRIORITY_ORDER: Record<string, number> = {
  high: 0,
  medium: 1,
  low: 2,
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

export function getGrowthAuditSourceEntityTypeLabel(
  type?: GrowthAuditSourceEntityType | string | null,
): string {
  if (!type) return "Non collegata";
  return SOURCE_ENTITY_TYPE_LABELS[type] ?? "Non collegata";
}

export function isGrowthAuditPageShopifyLinked(page: GrowthAuditPage): boolean {
  return Boolean(page.sourceEntityType);
}

export function getGrowthAuditShopifyLinkBadgeLabel(page: GrowthAuditPage): string {
  return isGrowthAuditPageShopifyLinked(page) ? "Collegata" : "Non collegata";
}

export function getGrowthAuditShopifyLinkBadgeClass(page: GrowthAuditPage): string {
  return isGrowthAuditPageShopifyLinked(page)
    ? "growth-audit-shopify-entity-badge growth-audit-shopify-entity-badge--linked"
    : "growth-audit-shopify-entity-badge growth-audit-shopify-entity-badge--unlinked";
}

export function getGrowthAuditShopifyEditorMicrocopy(
  page: GrowthAuditPage,
): string | null {
  if (!page.sourceEntityType) return null;
  if (
    page.sourceEntityType === "shopify_product" ||
    page.sourceEntityType === "shopify_collection"
  ) {
    return "Nel prossimo step potrai modificare title, meta description, alt immagini e altri campi Shopify direttamente da qui.";
  }
  if (
    page.sourceEntityType === "shopify_page" ||
    page.sourceEntityType === "shopify_article"
  ) {
    return "Modifica Shopify per questa tipologia in arrivo.";
  }
  return null;
}

export function getGrowthAuditInventoryFilterLabel(filter: GrowthAuditInventoryFilter): string {
  return INVENTORY_FILTER_LABELS[filter];
}

export function getGrowthAuditSourceBadgeClass(source?: string | null): string {
  switch (source) {
    case "seed":
      return "growth-audit-source-badge growth-audit-source-badge--seed";
    case "sitemap":
      return "growth-audit-source-badge growth-audit-source-badge--sitemap";
    case "shopify_product":
      return "growth-audit-source-badge growth-audit-source-badge--shopify-product";
    case "shopify_collection":
      return "growth-audit-source-badge growth-audit-source-badge--shopify-collection";
    case "shopify_page":
      return "growth-audit-source-badge growth-audit-source-badge--shopify-page";
    case "shopify_blog":
      return "growth-audit-source-badge growth-audit-source-badge--shopify-blog";
    default:
      return "growth-audit-source-badge growth-audit-source-badge--other";
  }
}

export function isGrowthAuditRunActive(status?: GrowthAuditRunStatus | string | null): boolean {
  return Boolean(
    status &&
      ["pending", "queued", "discovering", "classifying", "analyzing", "ready_for_analysis"].includes(
        status,
      ),
  );
}

export function isMyshopifyDomain(url: string): boolean {
  if (!url.trim()) return false;
  try {
    const trimmed = url.trim();
    const withProtocol =
      trimmed.startsWith("http://") || trimmed.startsWith("https://")
        ? trimmed
        : `https://${trimmed}`;
    const host = new URL(withProtocol).hostname.toLowerCase();
    return host.endsWith(".myshopify.com");
  } catch {
    return false;
  }
}

function resolvePublicRootUrl(url?: string | null): string | null {
  if (!url?.trim()) return null;
  const trimmed = url.trim();
  if (isMyshopifyDomain(trimmed)) return null;
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    return trimmed;
  }
  return `https://${trimmed}`;
}

export type GetDefaultRootUrlInput = {
  rootUrlOverride?: string | null;
  projectPublicSiteUrl?: string | null;
  activeRun?: { rootUrl?: string } | null;
  latestRun?: { rootUrl?: string } | null;
};

export function getDefaultRootUrl(input?: GetDefaultRootUrlInput): string {
  const override = input?.rootUrlOverride?.trim();
  if (override) {
    if (isMyshopifyDomain(override)) return "";
    return resolvePublicRootUrl(override) ?? "";
  }

  const fromProject = resolvePublicRootUrl(input?.projectPublicSiteUrl);
  if (fromProject) return fromProject;

  const fromActive = resolvePublicRootUrl(input?.activeRun?.rootUrl);
  if (fromActive) return fromActive;

  const fromLatest = resolvePublicRootUrl(input?.latestRun?.rootUrl);
  if (fromLatest) return fromLatest;

  return "";
}

export function formatGrowthAuditPublicSiteHostname(url?: string | null): string | null {
  const resolved = resolvePublicRootUrl(url);
  if (!resolved) return null;
  try {
    return new URL(resolved).hostname;
  } catch {
    return null;
  }
}

export function getGrowthAuditPublicDomainDisplay(
  project?: { publicSiteUrl?: string | null } | null,
  run?: { rootUrl?: string } | null,
): string {
  const fromProject = resolvePublicRootUrl(project?.publicSiteUrl);
  if (fromProject) return fromProject;

  return resolvePublicRootUrl(run?.rootUrl) ?? "Dominio pubblico non configurato";
}

function normalizePageTypeForFilter(pageType?: string | null): GrowthAuditInventoryFilter | "other" {
  if (!pageType) return "unknown";
  if (pageType === "homepage") return "homepage";
  if (pageType === "product") return "product";
  if (pageType === "collection") return "collection";
  if (pageType === "blog" || pageType === "blog_article" || pageType === "article") return "blog";
  if (pageType === "static_page" || pageType === "page") return "static_page";
  if (pageType === "unknown" || pageType === "other") return "unknown";
  return "other";
}

export function filterInventoryPages(
  pages: GrowthAuditPage[],
  filter: GrowthAuditInventoryFilter,
): GrowthAuditPage[] {
  if (filter === "all") return pages;
  return pages.filter((page) => normalizePageTypeForFilter(page.pageType) === filter);
}

export function getGrowthAuditScoreBand(score?: number | null): "none" | "good" | "warning" | "critical" {
  if (score == null) return "none";
  if (score >= 80) return "good";
  if (score >= 60) return "warning";
  return "critical";
}

export function getGrowthAuditScoreBadgeClass(score?: number | null): string {
  const band = getGrowthAuditScoreBand(score);
  return `growth-audit-score-badge growth-audit-score-badge--${band}`;
}

export function formatGrowthAuditScore(score?: number | null): string {
  if (score == null) return "—";
  return String(score);
}

export function filterInventoryPagesByScore(
  pages: GrowthAuditPage[],
  scoreFilter: GrowthAuditScoreFilter,
): GrowthAuditPage[] {
  if (scoreFilter === "all") return pages;
  return pages.filter((page) => {
    const band = getGrowthAuditScoreBand(page.score);
    if (scoreFilter === "critical") return band === "critical";
    if (scoreFilter === "warning") return band === "warning";
    if (scoreFilter === "good") return band === "good";
    return true;
  });
}

export function filterInventoryPagesByStatus(
  pages: GrowthAuditPage[],
  statusFilter: GrowthAuditPageStatusFilter,
): GrowthAuditPage[] {
  if (statusFilter === "all") return pages;
  return pages.filter((page) => page.status === statusFilter);
}

export function countFindingsByPageId(findings: GrowthAuditFinding[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const finding of findings) {
    if (!finding.pageId) continue;
    counts[finding.pageId] = (counts[finding.pageId] ?? 0) + 1;
  }
  return counts;
}

export function getTopPriorityFindings(findings: GrowthAuditFinding[], limit = 10): GrowthAuditFinding[] {
  return [...findings]
    .sort((a, b) => {
      const severityDiff =
        (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99);
      if (severityDiff !== 0) return severityDiff;
      return (a.title || "").localeCompare(b.title || "");
    })
    .slice(0, limit);
}

export function getTopOpenTasks(tasks: GrowthAuditTask[], limit = 10): GrowthAuditTask[] {
  return [...tasks]
    .filter((task) => task.status === "open")
    .sort((a, b) => {
      const priorityDiff =
        (PRIORITY_ORDER[a.priority] ?? 99) - (PRIORITY_ORDER[b.priority] ?? 99);
      if (priorityDiff !== 0) return priorityDiff;
      return (a.title || "").localeCompare(b.title || "");
    })
    .slice(0, limit);
}

export function getGrowthAuditSeverityBadgeClass(severity?: string | null): string {
  const normalized = severity || "medium";
  return `growth-audit-severity-badge growth-audit-severity-badge--${normalized}`;
}

export function getGrowthAuditAiKpiLabel(count?: number | null): string {
  if (count == null || count === 0) return "—";
  return String(count);
}

export function getTechnicalKpiItems(
  run?: {
    siteScore?: number | null;
    pagesDiscovered?: number;
    pagesAnalyzed?: number;
    summary?: GrowthAuditRunSummary | null;
  } | null,
  findingsCount?: number,
  tasksCount?: number,
) {
  const summary = run?.summary;
  const criticalHigh =
    (summary?.criticalFindings ?? 0) + (summary?.highFindings ?? 0) || findingsCount || 0;
  return [
    {
      label: "Score tecnico",
      value: run?.siteScore != null ? String(run.siteScore) : "—",
      score: run?.siteScore,
    },
    {
      label: "Pagine scoperte",
      value: String(run?.pagesDiscovered ?? summary?.pagesDiscovered ?? "—"),
    },
    {
      label: "Pagine analizzate",
      value: String(run?.pagesAnalyzed ?? summary?.pagesAnalyzed ?? "—"),
    },
    {
      label: "Pagine AI analizzate",
      value: getGrowthAuditAiKpiLabel(summary?.aiPagesAnalyzed),
    },
    {
      label: "Problemi critici/alti",
      value: criticalHigh > 0 ? String(criticalHigh) : "—",
    },
    {
      label: "Task aperti",
      value: String(summary?.tasksOpen ?? tasksCount ?? "—"),
    },
  ];
}

export function aggregatePageInventory(pages: GrowthAuditPage[]): GrowthAuditInventoryCounts {
  const counts: GrowthAuditInventoryCounts = {
    total: pages.length,
    homepage: 0,
    product: 0,
    collection: 0,
    blog: 0,
    staticPage: 0,
    unknown: 0,
    bySource: {},
    byStatus: {},
  };

  for (const page of pages) {
    const filterKey = normalizePageTypeForFilter(page.pageType);
    if (filterKey === "homepage") counts.homepage += 1;
    if (filterKey === "product") counts.product += 1;
    if (filterKey === "collection") counts.collection += 1;
    if (filterKey === "blog") counts.blog += 1;
    if (filterKey === "static_page") counts.staticPage += 1;
    if (filterKey === "unknown" || filterKey === "other") counts.unknown += 1;

    const source = page.source || "unknown";
    counts.bySource[source] = (counts.bySource[source] ?? 0) + 1;

    const status = page.status || "unknown";
    counts.byStatus[status] = (counts.byStatus[status] ?? 0) + 1;
  }

  return counts;
}

export function getInventoryMessage(
  pagesDiscovered: number,
  summary?: GrowthAuditRunSummary | null,
): string | null {
  if (summary?.message?.includes("Technical page scan completed")) {
    return "Scansione tecnica completata. Nel prossimo step aggiungeremo analisi AI/GEO/CRO per tipo pagina.";
  }
  if (summary?.warning) return summary.warning;
  if (pagesDiscovered > 1) {
    return "Inventario creato. La scansione tecnica analizza ogni pagina scoperta.";
  }
  if (pagesDiscovered === 1) {
    return "È stata trovata solo la pagina seed. Verifica sitemap o discovery Shopify.";
  }
  return null;
}

export function getInventoryKpiItems(
  pages: GrowthAuditPage[],
  summary?: GrowthAuditRunSummary | null,
) {
  const aggregated = aggregatePageInventory(pages);
  const pageTypes = summary?.pageTypes ?? {};

  return [
    { label: "Pagine scoperte", value: String(aggregated.total) },
    { label: "Homepage", value: String(pageTypes.homepage ?? aggregated.homepage) },
    { label: "Prodotti", value: String(pageTypes.product ?? aggregated.product) },
    { label: "Categorie", value: String(pageTypes.collection ?? aggregated.collection) },
    {
      label: "Blog/articoli",
      value: String(
        (pageTypes.blog ?? 0) +
          (pageTypes.blog_article ?? 0) +
          (pageTypes.article ?? 0) +
          aggregated.blog,
      ),
    },
    {
      label: "Statiche",
      value: String(
        (pageTypes.static_page ?? 0) + (pageTypes.page ?? 0) + aggregated.staticPage,
      ),
    },
    { label: "Sconosciute", value: String(pageTypes.unknown ?? aggregated.unknown) },
  ];
}

export interface GrowthAuditPageTechnicalMetadata {
  schemaTypes: string[];
  imagesTotal: number | null;
  imagesMissingAlt: number | null;
  linksInternal: number | null;
  linksExternal: number | null;
  robots: { noindex?: boolean; nofollow?: boolean; raw?: string } | null;
}

const SEVERITY_LABELS: Record<string, string> = {
  critical: "Critico",
  high: "Alta",
  medium: "Media",
  low: "Bassa",
  info: "Info",
};

const TASK_PRIORITY_LABELS: Record<string, string> = {
  high: "Alta",
  medium: "Media",
  low: "Bassa",
};

const OWNER_TYPE_LABELS: Record<string, string> = {
  seo: "SEO",
  content: "Contenuto",
  dev: "Sviluppo",
  design: "Design",
  ads: "Ads",
};

function readTechnicalBlock(page: GrowthAuditPage): Record<string, unknown> | null {
  const metadata = page.metadata as Record<string, unknown> | null | undefined;
  if (metadata?.technical && typeof metadata.technical === "object") {
    return metadata.technical as Record<string, unknown>;
  }
  const pageMetadata = (page as GrowthAuditPage & { pageMetadata?: Record<string, unknown> })
    .pageMetadata;
  if (pageMetadata?.technical && typeof pageMetadata.technical === "object") {
    return pageMetadata.technical as Record<string, unknown>;
  }
  return null;
}

export function getFindingsForPage(
  findings: GrowthAuditFinding[],
  pageId: string | null,
): GrowthAuditFinding[] {
  if (!pageId) return [];
  return findings.filter((finding) => finding.pageId === pageId);
}

export function getTasksForPage(
  tasks: GrowthAuditTask[],
  pageId: string | null,
): GrowthAuditTask[] {
  if (!pageId) return [];
  return tasks.filter((task) => task.pageId === pageId);
}

export function sortGrowthAuditFindings(findings: GrowthAuditFinding[]): GrowthAuditFinding[] {
  return [...findings].sort((a, b) => {
    const severityDiff =
      (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99);
    if (severityDiff !== 0) return severityDiff;
    return (a.title || "").localeCompare(b.title || "");
  });
}

export function sortGrowthAuditTasks(tasks: GrowthAuditTask[]): GrowthAuditTask[] {
  return [...tasks].sort((a, b) => {
    const priorityDiff =
      (PRIORITY_ORDER[a.priority] ?? 99) - (PRIORITY_ORDER[b.priority] ?? 99);
    if (priorityDiff !== 0) return priorityDiff;
    return (a.title || "").localeCompare(b.title || "");
  });
}

export function getGrowthAuditPageScoreLabel(score?: number | null): string {
  if (score == null) return "Non disponibile";
  if (score >= 80) return "Buona";
  if (score >= 60) return "Da migliorare";
  return "Critica";
}

export function getGrowthAuditFindingSeverityLabel(severity?: string | null): string {
  if (!severity) return "—";
  return SEVERITY_LABELS[severity] ?? severity;
}

export function getGrowthAuditTaskPriorityLabel(priority?: string | null): string {
  if (!priority) return "—";
  return TASK_PRIORITY_LABELS[priority] ?? priority;
}

export function getGrowthAuditOwnerTypeLabel(ownerType?: string | null): string {
  if (!ownerType) return "—";
  return OWNER_TYPE_LABELS[ownerType] ?? ownerType;
}

export function getGrowthAuditPageTechnicalMetadata(
  page: GrowthAuditPage,
): GrowthAuditPageTechnicalMetadata {
  const technical = readTechnicalBlock(page);
  const schemaTypes = Array.isArray(technical?.schemaTypes)
    ? (technical.schemaTypes as unknown[]).filter((item): item is string => typeof item === "string")
    : [];

  const readNumber = (key: string): number | null => {
    const value = technical?.[key];
    return typeof value === "number" ? value : null;
  };

  const robotsRaw = technical?.robots;
  const robots =
    robotsRaw && typeof robotsRaw === "object"
      ? (robotsRaw as { noindex?: boolean; nofollow?: boolean; raw?: string })
      : null;

  return {
    schemaTypes,
    imagesTotal: readNumber("imagesTotal"),
    imagesMissingAlt: readNumber("imagesMissingAlt"),
    linksInternal: readNumber("linksInternal"),
    linksExternal: readNumber("linksExternal"),
    robots,
  };
}

export function formatPageFindingsCount(count: number): string {
  if (count <= 0) return "Nessun problema";
  if (count === 1) return "1 problema";
  return `${count} problemi`;
}

export function getGrowthAuditPageInventoryStatusLabel(status?: string | null): string {
  if (!status) return "Non ancora scansionata";
  if (status === "analyzed") return "Analizzata";
  if (status === "failed") return "Fallita";
  if (status === "classified") return "Classificata";
  if (status === "pending" || status === "discovered" || status === "analyzing") {
    return "Non ancora scansionata";
  }
  return getGrowthAuditPageStatusLabel(status);
}

export type GrowthAuditImprovementStatus = "ok" | "warning" | "issue" | "unknown";

export interface GrowthAuditPageImprovementItem {
  key: string;
  label: string;
  status: GrowthAuditImprovementStatus;
  title: string;
  description: string;
  recommendation: string;
  howToValidate: string;
  evidence?: string;
}

const IMPROVEMENT_STATUS_LABELS: Record<GrowthAuditImprovementStatus, string> = {
  ok: "OK",
  warning: "Migliorabile",
  issue: "Problema",
  unknown: "Non disponibile",
};

const FINDING_KEYWORDS: Record<string, string[]> = {
  http: ["http status", "http"],
  title: ["title"],
  titleLength: ["lunghezza title", "title troppo", "title corto"],
  meta: ["meta description", "meta"],
  metaLength: ["lunghezza meta", "meta description"],
  h1: ["h1"],
  h1Count: ["h1 multipl", "più h1", "h1 singol"],
  canonical: ["canonical"],
  robots: ["noindex", "robots"],
  schema: ["json-ld", "schema", "structured data"],
  productSchema: ["product schema", "schema product"],
  collectionSchema: ["collection schema", "breadcrumb", "itemlist"],
  imagesAlt: ["alt", "immagini"],
  openGraph: ["open graph", "og:"],
};

function readTechnicalRaw(page: GrowthAuditPage): Record<string, unknown> | null {
  return readTechnicalBlock(page);
}

function findMatchingFinding(
  findings: GrowthAuditFinding[],
  keywords: string[],
): GrowthAuditFinding | undefined {
  return findings.find((finding) => {
    const haystack = `${finding.title} ${finding.description ?? ""}`.toLowerCase();
    return keywords.some((keyword) => haystack.includes(keyword));
  });
}

function elevateFromFinding(
  item: GrowthAuditPageImprovementItem,
  finding: GrowthAuditFinding | undefined,
): GrowthAuditPageImprovementItem {
  if (!finding) return item;
  const elevatedStatus: GrowthAuditImprovementStatus =
    finding.severity === "critical" || finding.severity === "high"
      ? "issue"
      : item.status === "ok"
        ? "warning"
        : item.status;
  return {
    ...item,
    status: elevatedStatus,
    recommendation: finding.recommendation || item.recommendation,
    howToValidate: finding.howToValidate || item.howToValidate,
    evidence: finding.evidence || item.evidence,
  };
}

function buildItem(
  partial: Omit<GrowthAuditPageImprovementItem, "label"> & { label?: string },
  findings: GrowthAuditFinding[],
  keywords: string[],
): GrowthAuditPageImprovementItem {
  const item: GrowthAuditPageImprovementItem = {
    label: partial.label ?? partial.title,
    ...partial,
  };
  return elevateFromFinding(item, findMatchingFinding(findings, keywords));
}

export function getGrowthAuditImprovementStatusLabel(
  status: GrowthAuditImprovementStatus,
): string {
  return IMPROVEMENT_STATUS_LABELS[status];
}

export function getGrowthAuditImprovementHeadline(page: GrowthAuditPage): {
  score: number | null;
  gap: number | null;
  label: string;
  text: string;
} {
  const score = page.score ?? null;
  const label = getGrowthAuditPageScoreLabel(score);
  const gap = score == null ? null : Math.max(0, 100 - score);
  const scoreText = score == null ? "—" : String(score);
  const gapText = gap == null ? "—" : String(gap);
  const text =
    score == null
      ? "Score non disponibile per questa pagina."
      : `Score ${scoreText}/100 — ${label}. Gap rispetto a 100: ${gapText} punti.`;
  return { score, gap, label, text };
}

export function getGrowthAuditImprovementSummaryText(page: GrowthAuditPage): string {
  const score = page.score;
  if (score == null) {
    return "Esegui una scansione tecnica per ottenere suggerimenti mirati.";
  }
  if (score >= 80) {
    return "La pagina non presenta problemi tecnici prioritari, ma può ancora migliorare su alcuni dettagli per aumentare solidità SEO.";
  }
  if (score >= 60) {
    return "Pagina da migliorare: ci sono elementi tecnici da sistemare per avvicinarsi a uno score ottimale.";
  }
  return "Pagina critica: intervenire sulle priorità indicate prima di ottimizzazioni minori.";
}

export function mapGrowthAuditPageToSeoEntity(
  page: GrowthAuditPage,
): { entityType: "product" | "collection"; entityId: string } | null {
  if (page.sourceEntityType === "shopify_product" && page.sourceEntityId) {
    return { entityType: "product", entityId: page.sourceEntityId };
  }
  if (page.sourceEntityType === "shopify_collection" && page.sourceEntityId) {
    return { entityType: "collection", entityId: page.sourceEntityId };
  }
  return null;
}

export function buildGrowthAuditPageImprovementItems(
  page: GrowthAuditPage,
  findings: GrowthAuditFinding[],
): GrowthAuditPageImprovementItem[] {
  const technical = getGrowthAuditPageTechnicalMetadata(page);
  const technicalRaw = readTechnicalRaw(page);
  const h1Count =
    typeof technicalRaw?.h1Count === "number" ? (technicalRaw.h1Count as number) : null;
  const openGraph =
    technicalRaw?.openGraph && typeof technicalRaw.openGraph === "object"
      ? (technicalRaw.openGraph as Record<string, unknown>)
      : null;

  const items: GrowthAuditPageImprovementItem[] = [];

  const httpStatus = page.httpStatus;
  if (httpStatus == null) {
    items.push(
      buildItem(
        {
          key: "http",
          label: "HTTP",
          status: "unknown",
          title: "HTTP status",
          description: "Lo status HTTP non è disponibile nella scansione.",
          recommendation: "Dato non disponibile nella scansione tecnica attuale.",
          howToValidate: "Riesegui la scansione tecnica della pagina.",
        },
        findings,
        FINDING_KEYWORDS.http,
      ),
    );
  } else {
    const httpOk = httpStatus >= 200 && httpStatus < 300;
    items.push(
      buildItem(
        {
          key: "http",
          label: "HTTP",
          status: httpOk ? "ok" : "issue",
          title: "HTTP status",
          description: httpOk
            ? `La pagina risponde con status ${httpStatus}.`
            : `La pagina risponde con status ${httpStatus}, fuori dal range 2xx.`,
          recommendation: httpOk
            ? "Nessuna azione richiesta."
            : "Verifica che la pagina sia raggiungibile e restituisca 200.",
          howToValidate: "Apri l'URL e controlla lo status nella scheda Network.",
          evidence: `HTTP ${httpStatus}`,
        },
        findings,
        FINDING_KEYWORDS.http,
      ),
    );
  }

  const title = page.title?.trim() ?? "";
  if (!title) {
    items.push(
      buildItem(
        {
          key: "title",
          label: "Title",
          status: "issue",
          title: "Title presente",
          description: "Il tag title non è presente o è vuoto.",
          recommendation: "Aggiungi un title descrittivo e unico di 30-65 caratteri.",
          howToValidate: "Ispeziona il sorgente HTML e verifica il tag <title>.",
        },
        findings,
        FINDING_KEYWORDS.title,
      ),
    );
  } else {
    items.push(
      buildItem(
        {
          key: "title",
          label: "Title",
          status: "ok",
          title: "Title presente",
          description: "Il title è presente.",
          recommendation: "Nessuna azione richiesta.",
          howToValidate: "Verifica che il title sia visibile nel sorgente HTML.",
          evidence: title,
        },
        findings,
        FINDING_KEYWORDS.title,
      ),
    );
    const titleLen = title.length;
    const titleLenOk = titleLen >= 30 && titleLen <= 65;
    items.push(
      buildItem(
        {
          key: "titleLength",
          label: "Title length",
          status: titleLenOk ? "ok" : "warning",
          title: "Lunghezza title",
          description: titleLenOk
            ? `Il title ha ${titleLen} caratteri (range consigliato 30-65).`
            : `Il title ha ${titleLen} caratteri, fuori dal range 30-65.`,
          recommendation: titleLenOk
            ? "Nessuna azione richiesta."
            : "Riscrivi il title tra 30 e 65 caratteri includendo keyword e brand.",
          howToValidate: "Conta i caratteri del title nel sorgente o in SERP preview.",
          evidence: `${titleLen} caratteri`,
        },
        findings,
        FINDING_KEYWORDS.titleLength,
      ),
    );
  }

  const meta = page.metaDescription?.trim() ?? "";
  if (!meta) {
    items.push(
      buildItem(
        {
          key: "meta",
          label: "Meta description",
          status: "issue",
          title: "Meta description",
          description: "La meta description non è presente o è vuota.",
          recommendation: "Aggiungi una meta description tra 80 e 165 caratteri.",
          howToValidate: "Verifica il tag meta description nel sorgente HTML.",
        },
        findings,
        FINDING_KEYWORDS.meta,
      ),
    );
  } else {
    items.push(
      buildItem(
        {
          key: "meta",
          label: "Meta description",
          status: "ok",
          title: "Meta description presente",
          description: "La meta description è presente.",
          recommendation: "Nessuna azione richiesta.",
          howToValidate: "Verifica il tag meta description nel sorgente.",
          evidence: meta.slice(0, 120) + (meta.length > 120 ? "…" : ""),
        },
        findings,
        FINDING_KEYWORDS.meta,
      ),
    );
    const metaLen = meta.length;
    const metaLenOk = metaLen >= 80 && metaLen <= 165;
    items.push(
      buildItem(
        {
          key: "metaLength",
          label: "Meta length",
          status: metaLenOk ? "ok" : "warning",
          title: "Lunghezza meta description",
          description: metaLenOk
            ? `La meta description ha ${metaLen} caratteri (range 80-165).`
            : `La meta description ha ${metaLen} caratteri, fuori dal range 80-165.`,
          recommendation: metaLenOk
            ? "Nessuna azione richiesta."
            : "Riscrivi la meta description tra 80 e 165 caratteri.",
          howToValidate: "Conta i caratteri della meta description.",
          evidence: `${metaLen} caratteri`,
        },
        findings,
        FINDING_KEYWORDS.metaLength,
      ),
    );
  }

  const h1 = page.h1?.trim() ?? "";
  items.push(
    buildItem(
      {
        key: "h1",
        label: "H1",
        status: h1 ? "ok" : "issue",
        title: "H1 presente",
        description: h1 ? "L'H1 è presente." : "L'H1 non è presente o è vuoto.",
        recommendation: h1
          ? "Nessuna azione richiesta."
          : "Aggiungi un H1 unico e descrittivo allineato al title.",
        howToValidate: "Verifica un solo tag <h1> nel sorgente HTML.",
        evidence: h1 || undefined,
      },
      findings,
      FINDING_KEYWORDS.h1,
    ),
  );

  if (h1Count == null) {
    items.push(
      buildItem(
        {
          key: "h1Count",
          label: "H1 singolo",
          status: "unknown",
          title: "H1 singolo",
          description: "Il conteggio H1 non è disponibile nella scansione.",
          recommendation: "Dato non disponibile nella scansione tecnica attuale.",
          howToValidate: "Ispeziona manualmente il numero di tag <h1> nella pagina.",
        },
        findings,
        FINDING_KEYWORDS.h1Count,
      ),
    );
  } else {
    items.push(
      buildItem(
        {
          key: "h1Count",
          label: "H1 singolo",
          status: h1Count === 1 ? "ok" : "warning",
          title: "H1 singolo",
          description:
            h1Count === 1
              ? "La pagina ha un solo H1."
              : `La pagina ha ${h1Count} tag H1.`,
          recommendation:
            h1Count === 1
              ? "Nessuna azione richiesta."
              : "Mantieni un solo H1 per pagina.",
          howToValidate: "Conta i tag <h1> nel sorgente HTML.",
          evidence: `${h1Count} H1`,
        },
        findings,
        FINDING_KEYWORDS.h1Count,
      ),
    );
  }

  const canonical = page.canonicalUrl?.trim() ?? "";
  items.push(
    buildItem(
      {
        key: "canonical",
        label: "Canonical",
        status: canonical ? "ok" : "warning",
        title: "Canonical URL",
        description: canonical
          ? "Il canonical è presente."
          : "Il canonical non è presente.",
        recommendation: canonical
          ? "Nessuna azione richiesta."
          : "Aggiungi un link rel=canonical verso l'URL preferito.",
        howToValidate: "Verifica <link rel=\"canonical\"> nel sorgente.",
        evidence: canonical || undefined,
      },
      findings,
      FINDING_KEYWORDS.canonical,
    ),
  );

  const noindex = technical.robots?.noindex === true;
  items.push(
    buildItem(
      {
        key: "robots",
        label: "Robots",
        status: noindex ? "issue" : "ok",
        title: "Robots noindex",
        description: noindex
          ? "La pagina ha noindex attivo."
          : "Nessuna restrizione noindex rilevata.",
        recommendation: noindex
          ? "Rimuovi noindex se la pagina deve essere indicizzata."
          : "Nessuna azione richiesta.",
        howToValidate: "Verifica meta robots o X-Robots-Tag.",
      },
      findings,
      FINDING_KEYWORDS.robots,
    ),
  );

  const hasSchema = technical.schemaTypes.length > 0;
  items.push(
    buildItem(
      {
        key: "schema",
        label: "JSON-LD",
        status: hasSchema ? "ok" : "warning",
        title: "JSON-LD / Schema",
        description: hasSchema
          ? `Schema rilevati: ${technical.schemaTypes.join(", ")}.`
          : "Nessuno schema JSON-LD rilevato.",
        recommendation: hasSchema
          ? "Nessuna azione richiesta."
          : "Aggiungi markup JSON-LD appropriato al tipo di pagina.",
        howToValidate: "Cerca script type=\"application/ld+json\" nel sorgente.",
        evidence: hasSchema ? technical.schemaTypes.join(", ") : undefined,
      },
      findings,
      FINDING_KEYWORDS.schema,
    ),
  );

  if (page.pageType === "product") {
    const hasProduct = technical.schemaTypes.some((t) =>
      t.toLowerCase().includes("product"),
    );
    items.push(
      buildItem(
        {
          key: "productSchema",
          label: "Product schema",
          status: hasProduct ? "ok" : "warning",
          title: "Schema Product",
          description: hasProduct
            ? "Schema Product rilevato."
            : "Schema Product non rilevato per pagina prodotto.",
          recommendation: hasProduct
            ? "Nessuna azione richiesta."
            : "Aggiungi markup Product con nome, immagine e offerta.",
          howToValidate: "Verifica JSON-LD Product nel sorgente o Rich Results Test.",
        },
        findings,
        FINDING_KEYWORDS.productSchema,
      ),
    );
  }

  if (page.pageType === "collection") {
    const hasCollectionSchema = technical.schemaTypes.some((t) => {
      const lower = t.toLowerCase();
      return (
        lower.includes("collection") ||
        lower.includes("breadcrumb") ||
        lower.includes("itemlist")
      );
    });
    items.push(
      buildItem(
        {
          key: "collectionSchema",
          label: "Collection schema",
          status: hasCollectionSchema ? "ok" : "warning",
          title: "Schema Collection",
          description: hasCollectionSchema
            ? "Schema collection/breadcrumb rilevato."
            : "Schema Collection o BreadcrumbList non rilevato.",
          recommendation: hasCollectionSchema
            ? "Nessuna azione richiesta."
            : "Aggiungi BreadcrumbList o CollectionPage markup.",
          howToValidate: "Verifica JSON-LD nel sorgente.",
        },
        findings,
        FINDING_KEYWORDS.collectionSchema,
      ),
    );
  }

  if (technical.imagesMissingAlt == null) {
    items.push(
      buildItem(
        {
          key: "imagesAlt",
          label: "Immagini alt",
          status: "unknown",
          title: "Immagini senza alt",
          description: "Il conteggio immagini senza alt non è disponibile.",
          recommendation: "Dato non disponibile nella scansione tecnica attuale.",
          howToValidate: "Ispeziona manualmente gli attributi alt delle immagini.",
        },
        findings,
        FINDING_KEYWORDS.imagesAlt,
      ),
    );
  } else {
    const missingAlt = technical.imagesMissingAlt;
    items.push(
      buildItem(
        {
          key: "imagesAlt",
          label: "Immagini alt",
          status: missingAlt === 0 ? "ok" : "warning",
          title: "Immagini senza alt",
          description:
            missingAlt === 0
              ? "Tutte le immagini rilevate hanno attributo alt."
              : `${missingAlt} immagini senza attributo alt.`,
          recommendation:
            missingAlt === 0
              ? "Nessuna azione richiesta."
              : "Aggiungi testi alt descrittivi a tutte le immagini.",
          howToValidate: "Verifica attributi alt nel sorgente o DevTools.",
          evidence: missingAlt === 0 ? undefined : `${missingAlt} senza alt`,
        },
        findings,
        FINDING_KEYWORDS.imagesAlt,
      ),
    );
  }

  if (openGraph) {
    const hasOg =
      Boolean(openGraph.title) || Boolean(openGraph.description) || Boolean(openGraph.image);
    items.push(
      buildItem(
        {
          key: "openGraph",
          label: "Open Graph",
          status: hasOg ? "ok" : "warning",
          title: "Open Graph",
          description: hasOg
            ? "Tag Open Graph rilevati."
            : "Tag Open Graph incompleti o assenti.",
          recommendation: hasOg
            ? "Nessuna azione richiesta."
            : "Aggiungi og:title, og:description e og:image.",
          howToValidate: "Verifica meta property og:* nel sorgente.",
        },
        findings,
        FINDING_KEYWORDS.openGraph,
      ),
    );
  } else {
    items.push(
      buildItem(
        {
          key: "openGraph",
          label: "Open Graph",
          status: "unknown",
          title: "Open Graph",
          description: "I dati Open Graph non sono disponibili nella scansione persistita.",
          recommendation: "Dato non disponibile nella scansione tecnica attuale.",
          howToValidate: "Verifica manualmente meta property og:* nel sorgente.",
        },
        findings,
        FINDING_KEYWORDS.openGraph,
      ),
    );
  }

  return items;
}

export type GrowthAuditPriorityActionCategory =
  | "technical"
  | "seo"
  | "content"
  | "geo"
  | "cro"
  | "ads"
  | "shopify"
  | "images"
  | "schema"
  | "unknown";

export type GrowthAuditPriorityActionPriority =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "info";

export type GrowthAuditPriorityActionSource =
  | "finding"
  | "task"
  | "improvement"
  | "ai_result";

export type GrowthAuditPriorityActionOwnerType =
  | "seo"
  | "content"
  | "dev"
  | "design"
  | "ads"
  | "unknown";

export type GrowthAuditPriorityActionEffort = "low" | "medium" | "high" | "unknown";

export type GrowthAuditPriorityAction = {
  id: string;
  source: GrowthAuditPriorityActionSource;
  category: GrowthAuditPriorityActionCategory;
  priority: GrowthAuditPriorityActionPriority;
  ownerType: GrowthAuditPriorityActionOwnerType;
  effort: GrowthAuditPriorityActionEffort;
  title: string;
  description: string;
  whyItMatters?: string;
  evidence?: string;
  recommendation: string;
  howToValidate?: string;
  whereToFix?: string;
  relatedFindingId?: string;
  relatedTaskId?: string;
  status?: string;
};

const PRIORITY_ACTION_CATEGORY_ORDER: Record<GrowthAuditPriorityActionCategory, number> = {
  cro: 0,
  ads: 1,
  geo: 2,
  content: 3,
  seo: 4,
  shopify: 5,
  images: 6,
  schema: 7,
  technical: 8,
  unknown: 9,
};

const OWNER_TYPE_ORDER: Record<GrowthAuditPriorityActionOwnerType, number> = {
  ads: 0,
  content: 1,
  design: 2,
  seo: 3,
  dev: 4,
  unknown: 5,
};

const EFFORT_ORDER: Record<GrowthAuditPriorityActionEffort, number> = {
  low: 0,
  medium: 1,
  high: 2,
  unknown: 3,
};

const PRIORITY_ACTION_LABELS: Record<GrowthAuditPriorityActionPriority, string> = {
  critical: "Critico",
  high: "Alto",
  medium: "Medio",
  low: "Basso",
  info: "Info",
};

const EFFORT_LABELS: Record<GrowthAuditPriorityActionEffort, string> = {
  low: "Basso",
  medium: "Medio",
  high: "Alto",
  unknown: "—",
};

const CATEGORY_LABELS: Record<GrowthAuditPriorityActionCategory, string> = {
  technical: "Tecnico",
  seo: "SEO",
  content: "Contenuto",
  geo: "GEO",
  cro: "CRO",
  ads: "Ads",
  shopify: "Shopify",
  images: "Immagini",
  schema: "Schema",
  unknown: "Altro",
};

const EXCLUDED_ITEM_STATUSES = new Set(["completed", "dismissed", "superseded"]);

function _normalizePriorityText(value?: string | null): string {
  return (value ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

export function normalizeGrowthAuditPriorityDedupeKey(input: {
  title: string;
  category: GrowthAuditPriorityActionCategory;
  recommendation?: string | null;
}): string {
  return [
    _normalizePriorityText(input.title),
    input.category,
    _normalizePriorityText(input.recommendation),
  ].join("|");
}

function _normalizePriorityLevel(value?: string | null): GrowthAuditPriorityActionPriority {
  const normalized = (value ?? "").toLowerCase();
  if (
    normalized === "critical" ||
    normalized === "high" ||
    normalized === "medium" ||
    normalized === "low" ||
    normalized === "info"
  ) {
    return normalized;
  }
  return "medium";
}

function _normalizeCategory(value?: string | null): GrowthAuditPriorityActionCategory {
  const normalized = (value ?? "").toLowerCase();
  if (normalized in CATEGORY_LABELS) {
    return normalized as GrowthAuditPriorityActionCategory;
  }
  if (normalized === "task") return "unknown";
  return "unknown";
}

function _normalizeOwnerType(value?: string | null): GrowthAuditPriorityActionOwnerType {
  const normalized = (value ?? "").toLowerCase();
  if (
    normalized === "seo" ||
    normalized === "content" ||
    normalized === "dev" ||
    normalized === "design" ||
    normalized === "ads"
  ) {
    return normalized;
  }
  return "unknown";
}

function _normalizeEffort(value?: string | null): GrowthAuditPriorityActionEffort {
  const normalized = (value ?? "").toLowerCase();
  if (normalized === "low" || normalized === "medium" || normalized === "high") {
    return normalized;
  }
  return "unknown";
}

function _inferOwnerTypeFromCategory(
  category: GrowthAuditPriorityActionCategory,
): GrowthAuditPriorityActionOwnerType {
  if (category === "ads") return "ads";
  if (category === "cro" || category === "content" || category === "geo") return "content";
  if (category === "technical" || category === "schema" || category === "images") return "dev";
  if (category === "seo" || category === "shopify") return "seo";
  return "unknown";
}

function _pageHasAiAnalysis(
  page: GrowthAuditPage,
  aiResults?: GrowthAuditPageResult[],
): boolean {
  if (page.metadata?.ai && typeof page.metadata.ai === "object") return true;
  return Boolean(aiResults?.some((result) => result.status === "completed"));
}

function _isCommercePage(page: GrowthAuditPage): boolean {
  return page.pageType === "product" || page.pageType === "landing_page";
}

function _comparePriorityActions(
  a: GrowthAuditPriorityAction,
  b: GrowthAuditPriorityAction,
  page: GrowthAuditPage,
  hasAiAnalysis: boolean,
): number {
  const priorityDiff =
    (SEVERITY_ORDER[a.priority] ?? 99) - (SEVERITY_ORDER[b.priority] ?? 99);
  if (priorityDiff !== 0) return priorityDiff;

  if (_isCommercePage(page)) {
    const categoryDiff =
      (PRIORITY_ACTION_CATEGORY_ORDER[a.category] ?? 99) -
      (PRIORITY_ACTION_CATEGORY_ORDER[b.category] ?? 99);
    if (categoryDiff !== 0) return categoryDiff;
  } else if (hasAiAnalysis) {
    const geoBoost = (category: GrowthAuditPriorityActionCategory) =>
      category === "geo" ? -1 : 0;
    const geoDiff = geoBoost(a.category) - geoBoost(b.category);
    if (geoDiff !== 0) return geoDiff;
  }

  if (_isCommercePage(page)) {
    const ownerDiff =
      (OWNER_TYPE_ORDER[a.ownerType] ?? 99) - (OWNER_TYPE_ORDER[b.ownerType] ?? 99);
    if (ownerDiff !== 0) return ownerDiff;
  }

  const effortDiff = (EFFORT_ORDER[a.effort] ?? 99) - (EFFORT_ORDER[b.effort] ?? 99);
  if (effortDiff !== 0) return effortDiff;

  return a.title.localeCompare(b.title);
}

function _dedupePriorityActions(actions: GrowthAuditPriorityAction[]): GrowthAuditPriorityAction[] {
  const seen = new Set<string>();
  const result: GrowthAuditPriorityAction[] = [];
  for (const action of actions) {
    const key = normalizeGrowthAuditPriorityDedupeKey({
      title: action.title,
      category: action.category,
      recommendation: action.recommendation,
    });
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(action);
  }
  return result;
}

function _findingToPriorityAction(finding: GrowthAuditFinding): GrowthAuditPriorityAction {
  const category = _normalizeCategory(finding.category);
  const priority = _normalizePriorityLevel(finding.severity);
  const ownerType = _normalizeOwnerType(finding.metadata?.ownerType as string | undefined) ||
    _inferOwnerTypeFromCategory(category);
  const action: GrowthAuditPriorityAction = {
    id: `finding-${finding.id}`,
    source: "finding",
    category,
    priority,
    ownerType,
    effort: _normalizeEffort(finding.effort),
    title: finding.title,
    description: finding.description ?? "",
    whyItMatters: finding.impact ? `Impatto stimato: ${finding.impact}` : undefined,
    evidence: finding.evidence ?? undefined,
    recommendation: finding.recommendation ?? "Nessuna raccomandazione disponibile.",
    howToValidate: finding.howToValidate ?? undefined,
    relatedFindingId: finding.id,
    status: finding.status,
  };
  return action;
}

function _taskToPriorityAction(task: GrowthAuditTask): GrowthAuditPriorityAction {
  const priority = _normalizePriorityLevel(task.priority);
  const ownerType = _normalizeOwnerType(task.ownerType);
  const action: GrowthAuditPriorityAction = {
    id: `task-${task.id}`,
    source: "task",
    category: "unknown",
    priority,
    ownerType,
    effort: _normalizeEffort(task.estimatedEffort),
    title: task.title,
    description: task.description ?? "",
    recommendation: task.description?.trim() || task.title,
    howToValidate: undefined,
    relatedTaskId: task.id,
    status: task.status,
  };
  return action;
}

function _improvementToPriorityAction(
  item: GrowthAuditPageImprovementItem,
): GrowthAuditPriorityAction {
  const category = _normalizeCategory(item.label);
  const priority: GrowthAuditPriorityActionPriority =
    item.status === "issue" ? "high" : "medium";
  const action: GrowthAuditPriorityAction = {
    id: `improvement-${item.key}`,
    source: "improvement",
    category,
    priority,
    ownerType: _inferOwnerTypeFromCategory(category),
    effort: "medium",
    title: item.title,
    description: item.description,
    evidence: item.evidence,
    recommendation: item.recommendation,
    howToValidate: item.howToValidate,
    status: item.status,
  };
  return action;
}

type InlineAiFinding = {
  category?: string;
  severity?: string;
  title?: string;
  description?: string;
  evidence?: string;
  recommendation?: string;
  howToValidate?: string;
  impact?: string;
  effort?: string;
};

function _aiInlineFindingToAction(
  finding: InlineAiFinding,
  resultId: string,
  index: number,
): GrowthAuditPriorityAction | null {
  const title = (finding.title ?? "").trim();
  if (!title) return null;
  const category = _normalizeCategory(finding.category);
  const priority = _normalizePriorityLevel(finding.severity);
  const action: GrowthAuditPriorityAction = {
    id: `ai-${resultId}-${index}`,
    source: "ai_result",
    category,
    priority,
    ownerType: _inferOwnerTypeFromCategory(category),
    effort: _normalizeEffort(finding.effort),
    title,
    description: finding.description ?? "",
    whyItMatters: finding.impact ? `Impatto stimato: ${finding.impact}` : undefined,
    evidence: finding.evidence,
    recommendation: finding.recommendation ?? "Nessuna raccomandazione disponibile.",
    howToValidate: finding.howToValidate,
    status: "open",
  };
  return action;
}

export function buildGrowthAuditPriorityActions(input: {
  page: GrowthAuditPage;
  findings: GrowthAuditFinding[];
  tasks: GrowthAuditTask[];
  improvementItems: GrowthAuditPageImprovementItem[];
  aiResults?: GrowthAuditPageResult[];
}): GrowthAuditPriorityAction[] {
  const { page, findings, tasks, improvementItems, aiResults } = input;
  const hasAiAnalysis = _pageHasAiAnalysis(page, aiResults);

  const openFindings = findings.filter(
    (finding) => finding.status === "open" && !EXCLUDED_ITEM_STATUSES.has(finding.status),
  );
  const openTasks = tasks.filter(
    (task) => task.status === "open" && !EXCLUDED_ITEM_STATUSES.has(task.status),
  );
  const improvementActions = improvementItems
    .filter((item) => item.status === "issue" || item.status === "warning")
    .map(_improvementToPriorityAction);

  const findingDedupeKeys = new Set(
    openFindings.map((finding) =>
      normalizeGrowthAuditPriorityDedupeKey({
        title: finding.title,
        category: _normalizeCategory(finding.category),
        recommendation: finding.recommendation,
      }),
    ),
  );

  const aiInlineActions: GrowthAuditPriorityAction[] = [];
  for (const result of aiResults ?? []) {
    if (result.status !== "completed") continue;
    const inlineFindings = Array.isArray(result.findings) ? result.findings : [];
    inlineFindings.forEach((rawFinding, index) => {
      if (!rawFinding || typeof rawFinding !== "object") return;
      const finding = rawFinding as InlineAiFinding;
      const category = _normalizeCategory(finding.category);
      const dedupeKey = normalizeGrowthAuditPriorityDedupeKey({
        title: finding.title ?? "",
        category,
        recommendation: finding.recommendation,
      });
      if (findingDedupeKeys.has(dedupeKey)) return;
      const action = _aiInlineFindingToAction(finding, result.id, index);
      if (action) {
        aiInlineActions.push(action);
        findingDedupeKeys.add(dedupeKey);
      }
    });
  }

  const rawActions: GrowthAuditPriorityAction[] = [
    ...openFindings.map((finding) => {
      const action = _findingToPriorityAction(finding);
      return { ...action, whereToFix: getGrowthAuditWhereToFix(action, page) };
    }),
    ...openTasks.map((task) => {
      const action = _taskToPriorityAction(task);
      return { ...action, whereToFix: getGrowthAuditWhereToFix(action, page) };
    }),
    ...improvementActions.map((action) => ({
      ...action,
      whereToFix: getGrowthAuditWhereToFix(action, page),
    })),
    ...aiInlineActions.map((action) => ({
      ...action,
      whereToFix: getGrowthAuditWhereToFix(action, page),
    })),
  ];

  const deduped = _dedupePriorityActions(rawActions);
  return deduped.sort((a, b) => _comparePriorityActions(a, b, page, hasAiAnalysis));
}

/** @deprecated Use buildGrowthAuditPriorityActions instead */
export function buildGrowthAuditPagePriorityActions(
  page: GrowthAuditPage,
  findings: GrowthAuditFinding[],
  tasks: GrowthAuditTask[],
): GrowthAuditPriorityAction[] {
  return buildGrowthAuditPriorityActions({
    page,
    findings,
    tasks,
    improvementItems: buildGrowthAuditPageImprovementItems(page, findings),
  });
}

export function getGrowthAuditPriorityActionLabel(
  priority: GrowthAuditPriorityActionPriority | string,
): string {
  return PRIORITY_ACTION_LABELS[priority as GrowthAuditPriorityActionPriority] ?? priority;
}

export function getGrowthAuditPriorityActionBadgeClass(
  priority: GrowthAuditPriorityActionPriority | string,
): string {
  const normalized = _normalizePriorityLevel(priority);
  return `growth-audit-priority-action-card growth-audit-priority-action-card--${normalized}`;
}

export function getGrowthAuditPriorityActionCategoryLabel(
  category: GrowthAuditPriorityActionCategory | string,
): string {
  return CATEGORY_LABELS[category as GrowthAuditPriorityActionCategory] ?? category;
}

export function getGrowthAuditEffortLabel(
  effort: GrowthAuditPriorityActionEffort | string,
): string {
  return EFFORT_LABELS[effort as GrowthAuditPriorityActionEffort] ?? effort;
}

export function getGrowthAuditWhereToFix(
  action: GrowthAuditPriorityAction,
  page: GrowthAuditPage,
): string {
  if (action.whereToFix) return action.whereToFix;

  const haystack = `${action.title} ${action.description} ${action.recommendation} ${action.category}`
    .toLowerCase();

  if (
    haystack.includes("title") ||
    haystack.includes("meta") ||
    haystack.includes("canonical") ||
    haystack.includes("h1")
  ) {
    return "Modifica Shopify → campi SEO / contenuto";
  }
  if (haystack.includes("alt") || haystack.includes("immagin")) {
    return "Modifica Shopify → immagini/alt";
  }
  if (haystack.includes("schema") || action.category === "schema") {
    return "Tema Shopify / dati strutturati";
  }
  if (
    action.category === "cro" ||
    haystack.includes("trust") ||
    haystack.includes("cta") ||
    haystack.includes("conversion")
  ) {
    return "Modifica Shopify → descrizione prodotto o sezioni pagina";
  }
  if (action.category === "geo" || action.category === "content") {
    return "Contenuto pagina / FAQ / struttura semantica";
  }
  if (
    action.category === "technical" ||
    action.ownerType === "dev" ||
    haystack.includes("performance")
  ) {
    return "Sviluppo / tema Shopify";
  }
  if (mapGrowthAuditPageToSeoEntity(page)) {
    return "Modifica Shopify → campi SEO / contenuto";
  }
  return "Contenuto pagina / implementazione on-page";
}

export function getGrowthAuditPageAiMetadata(
  page: GrowthAuditPage,
): GrowthAuditPageAiMetadata | null {
  const ai = page.metadata?.ai;
  if (!ai || typeof ai !== "object") return null;
  return ai as GrowthAuditPageAiMetadata;
}

export function hasGrowthAuditPageAiAnalysis(page: GrowthAuditPage): boolean {
  const aiMeta = getGrowthAuditPageAiMetadata(page);
  return Boolean(aiMeta?.analyzedAt || aiMeta?.latestResultId || aiMeta?.latestScore != null);
}

export function getGrowthAuditPagePerformanceMetadata(
  page: GrowthAuditPage,
): GrowthAuditPagePerformanceMetadata | null {
  const performance = page.metadata?.performance;
  if (!performance || typeof performance !== "object") return null;
  return performance as GrowthAuditPagePerformanceMetadata;
}

export function hasGrowthAuditPagePerformanceAnalysis(page: GrowthAuditPage): boolean {
  const performanceMeta = getGrowthAuditPagePerformanceMetadata(page);
  return Boolean(
    performanceMeta?.analyzedAt ||
      performanceMeta?.latestResultId ||
      performanceMeta?.latestScore != null ||
      page.performanceScore != null,
  );
}

export function getGrowthAuditPageSearchConsoleMetadata(
  page: GrowthAuditPage,
): GrowthAuditPageSearchConsoleMetadata | null {
  const searchConsole = page.metadata?.searchConsole;
  if (!searchConsole || typeof searchConsole !== "object") return null;
  return searchConsole as GrowthAuditPageSearchConsoleMetadata;
}

export function hasGrowthAuditPageSearchConsoleData(page: GrowthAuditPage): boolean {
  const meta = getGrowthAuditPageSearchConsoleMetadata(page);
  return Boolean(
    meta &&
      ((meta.impressions ?? 0) > 0 ||
        (meta.clicks ?? 0) > 0 ||
        (meta.topQueries?.length ?? 0) > 0),
  );
}

function _getSearchConsolePriorityBoost(page: GrowthAuditPage): number {
  const meta = getGrowthAuditPageSearchConsoleMetadata(page);
  if (!meta) return 0;

  let boost = 0;
  const impressions = meta.impressions ?? 0;
  const ctr = meta.ctr ?? 0;
  const position = meta.position ?? 0;

  if (impressions >= 100 && ctr < 0.02) boost += 12;
  if (position >= 4 && position <= 15 && impressions >= 20) boost += 8;
  if (impressions > 0 && (meta.clicks ?? 0) === 0) boost += 6;
  if ((meta.topQueries?.length ?? 0) > 0) boost += 4;

  return Math.min(boost, 20);
}

export type GrowthAuditDashboardKpiItem = {
  label: string;
  value: string;
  score?: number | null;
  meta?: string;
};

export function computeGrowthAuditPageScoreAverages(pages: GrowthAuditPage[]): {
  geoAverage: number | null;
  croAverage: number | null;
  adsAverage: number | null;
} {
  const geoScores: number[] = [];
  const croScores: number[] = [];
  const adsScores: number[] = [];

  for (const page of pages) {
    const aiMeta = getGrowthAuditPageAiMetadata(page);
    const geo = aiMeta?.geoScore ?? page.geoScore;
    const cro = aiMeta?.croScore ?? page.croScore;
    const ads = aiMeta?.adsReadinessScore;
    if (geo != null) geoScores.push(geo);
    if (cro != null) croScores.push(cro);
    if (ads != null) adsScores.push(ads);
  }

  const average = (values: number[]) =>
    values.length > 0
      ? Math.round(values.reduce((sum, value) => sum + value, 0) / values.length)
      : null;

  return {
    geoAverage: average(geoScores),
    croAverage: average(croScores),
    adsAverage: average(adsScores),
  };
}

export function getGrowthAuditDashboardKpiItems(
  run?: {
    siteScore?: number | null;
    pagesAnalyzed?: number;
    performanceScore?: number | null;
    summary?: GrowthAuditRunSummary | null;
  } | null,
  pages: GrowthAuditPage[] = [],
  findingsCount?: number,
  tasksCount?: number,
): GrowthAuditDashboardKpiItem[] {
  const summary = run?.summary;
  const technicalScore = run?.siteScore ?? summary?.averageTechnicalScore ?? null;
  const criticalHigh =
    (summary?.criticalFindings ?? 0) + (summary?.highFindings ?? 0) || findingsCount || 0;
  const aiPagesFromPages = pages.filter((page) => hasGrowthAuditPageAiAnalysis(page)).length;
  const aiPagesAnalyzed =
    summary?.aiPagesAnalyzed ?? (aiPagesFromPages > 0 ? aiPagesFromPages : null);
  const { geoAverage, croAverage, adsAverage } = computeGrowthAuditPageScoreAverages(pages);
  const formatAverage = (average: number | null) => (average != null ? String(average) : "—");
  const performanceScore =
    summary?.averagePerformanceScore ?? run?.performanceScore ?? null;

  return [
    {
      label: "Score tecnico",
      value: technicalScore != null ? String(technicalScore) : "—",
      score: technicalScore,
    },
    {
      label: "Pagine analizzate",
      value: String(run?.pagesAnalyzed ?? summary?.pagesAnalyzed ?? "—"),
    },
    {
      label: "Pagine AI analizzate",
      value: getGrowthAuditAiKpiLabel(aiPagesAnalyzed),
    },
    {
      label: "Problemi critici/alti",
      value: criticalHigh > 0 ? String(criticalHigh) : "—",
    },
    {
      label: "Task aperti",
      value: String(summary?.tasksOpen ?? tasksCount ?? "—"),
    },
    {
      label: "GEO medio",
      value: formatAverage(geoAverage),
    },
    {
      label: "CRO medio",
      value: formatAverage(croAverage),
    },
    {
      label: "Ads readiness medio",
      value: formatAverage(adsAverage),
    },
    {
      label: "Performance",
      value: performanceScore != null ? String(performanceScore) : "—",
      score: performanceScore,
      meta: performanceScore == null ? "Non analizzato" : undefined,
    },
    {
      label: "Click organici",
      value:
        summary?.searchConsole?.totalClicks != null
          ? String(summary.searchConsole.totalClicks)
          : "—",
    },
    {
      label: "Impression",
      value:
        summary?.searchConsole?.totalImpressions != null
          ? String(summary.searchConsole.totalImpressions)
          : "—",
    },
    {
      label: "CTR medio",
      value:
        summary?.searchConsole?.averageCtr != null
          ? `${(summary.searchConsole.averageCtr * 100).toFixed(2)}%`
          : "—",
    },
    {
      label: "Posizione media",
      value:
        summary?.searchConsole?.averagePosition != null
          ? summary.searchConsole.averagePosition.toFixed(1)
          : "—",
    },
    {
      label: "Pagine con dati GSC",
      value:
        summary?.searchConsole?.pagesWithData != null
          ? String(summary.searchConsole.pagesWithData)
          : "—",
    },
  ];
}

export type GrowthAuditPagePriorityLevel = "critical" | "high" | "medium" | "low";

export type GrowthAuditPagePriorityItem = {
  pageId: string;
  url: string;
  title: string;
  pageType: string;
  pageTypeLabel: string;
  sourceLabel: string;
  score: number | null;
  aiScore: number | null;
  geoScore: number | null;
  croScore: number | null;
  adsReadinessScore: number | null;
  openFindings: number;
  highPriorityFindings: number;
  openTasks: number;
  isShopifyLinked: boolean;
  sourceEntityType?: string | null;
  priorityScore: number;
  priorityLevel: GrowthAuditPagePriorityLevel;
  reasons: string[];
  recommendedNextAction: string;
};

const PRIORITY_LEVEL_LABELS: Record<GrowthAuditPagePriorityLevel, string> = {
  critical: "Critico",
  high: "Alto",
  medium: "Medio",
  low: "Basso",
};

const SYSTEM_PAGE_TYPES = new Set([
  "policy",
  "cart",
  "checkout",
  "search",
  "account",
  "policy_page",
  "system_page",
]);

const STRATEGIC_AI_PAGE_TYPES = new Set([
  "product",
  "collection",
  "landing_page",
  "homepage",
]);

function _getBusinessPageTypeBoost(pageType: string): number {
  const normalized = pageType.toLowerCase();
  if (normalized === "product") return 18;
  if (normalized === "collection") return 14;
  if (normalized === "landing_page") return 16;
  if (normalized === "homepage") return 12;
  if (normalized === "blog_article" || normalized === "blog" || normalized === "article") return 8;
  if (normalized === "static_page" || normalized === "page") return 4;
  if (SYSTEM_PAGE_TYPES.has(normalized)) return -20;
  return 0;
}

function _getTechnicalScoreBoost(score: number | null | undefined): number {
  if (score == null) return 12;
  if (score < 60) return 35;
  if (score < 80) return 20;
  if (score < 90) return 8;
  return 0;
}

function _getTaskPriorityBoost(priority: string): number {
  const normalized = priority.toLowerCase();
  if (normalized === "high") return 10;
  if (normalized === "medium") return 5;
  if (normalized === "low") return 2;
  return 0;
}

function _getFindingSeverityBoost(severity: string): number {
  const normalized = severity.toLowerCase();
  if (normalized === "critical") return 25;
  if (normalized === "high") return 15;
  if (normalized === "medium") return 6;
  if (normalized === "low") return 2;
  return 0;
}

function _resolvePriorityLevel(score: number): GrowthAuditPagePriorityLevel {
  if (score >= 70) return "critical";
  if (score >= 45) return "high";
  if (score >= 20) return "medium";
  return "low";
}

function _pageHasSeoContentIssues(
  pageFindings: GrowthAuditFinding[],
  page: GrowthAuditPage,
): boolean {
  const haystack = pageFindings
    .map((f) => `${f.title} ${f.category} ${f.description ?? ""}`)
    .join(" ")
    .toLowerCase();
  if (
    haystack.includes("title") ||
    haystack.includes("meta") ||
    haystack.includes("immagin") ||
    haystack.includes("alt") ||
    haystack.includes("h1")
  ) {
    return true;
  }
  const titleLen = page.title?.length ?? 0;
  const metaLen = page.metaDescription?.length ?? 0;
  return titleLen < 30 || titleLen > 65 || metaLen < 80 || metaLen > 165;
}

function _buildPagePriorityReasons(input: {
  page: GrowthAuditPage;
  pageFindings: GrowthAuditFinding[];
  openTasks: number;
  highPriorityFindings: number;
  hasAiAnalysis: boolean;
  aiMeta: GrowthAuditPageAiMetadata | null;
}): string[] {
  const { page, openTasks, highPriorityFindings, hasAiAnalysis, aiMeta } = input;
  const reasons: string[] = [];

  if (page.score != null && page.score < 60) {
    reasons.push("Score tecnico basso");
  }
  if (highPriorityFindings > 0) {
    reasons.push("Problemi ad alta priorità");
  }
  if (
    isGrowthAuditPageShopifyLinked(page) &&
    (page.pageType === "product" || page.pageType === "collection")
  ) {
    reasons.push("Pagina prodotto collegata a Shopify");
  }
  if (
    !hasAiAnalysis &&
    STRATEGIC_AI_PAGE_TYPES.has((page.pageType ?? "").toLowerCase())
  ) {
    reasons.push("Non ancora analizzata con AI/GEO/CRO");
  }
  const croScore = aiMeta?.croScore ?? page.croScore;
  if (croScore != null && croScore < 70) {
    reasons.push("CRO sotto soglia");
  }
  const geoScore = aiMeta?.geoScore ?? page.geoScore;
  if (geoScore != null && geoScore < 70) {
    reasons.push("GEO sotto soglia");
  }
  if (openTasks > 0) {
    reasons.push("Task aperti");
  }
  if (
    !hasGrowthAuditPagePerformanceAnalysis(page) &&
    (page.pageType === "product" || page.pageType === "landing")
  ) {
    reasons.push("Performance non ancora analizzata");
  }

  const gscMeta = getGrowthAuditPageSearchConsoleMetadata(page);
  if (gscMeta) {
    const impressions = gscMeta.impressions ?? 0;
    const ctr = gscMeta.ctr ?? 0;
    if (impressions >= 100 && ctr < 0.02) {
      reasons.push("Opportunità CTR da Search Console");
    }
    if ((gscMeta.topQueries?.length ?? 0) > 0) {
      reasons.push("Query reali disponibili");
    }
  }

  if (page.pageType === "collection" && page.score != null && page.score < 80) {
    reasons.push("Collection commerciale da ottimizzare");
  }

  const unique = [...new Set(reasons)];
  return unique.slice(0, 4);
}

function _buildRecommendedNextAction(input: {
  page: GrowthAuditPage;
  pageFindings: GrowthAuditFinding[];
  hasAiAnalysis: boolean;
}): string {
  const { page, pageFindings, hasAiAnalysis } = input;
  const shopifyLinked = isGrowthAuditPageShopifyLinked(page);
  const isCommerce =
    page.pageType === "product" || page.pageType === "collection";

  if (shopifyLinked && isCommerce && _pageHasSeoContentIssues(pageFindings, page)) {
    return "Apri la scheda e correggi da Modifica Shopify";
  }
  if (
    !hasAiAnalysis &&
    STRATEGIC_AI_PAGE_TYPES.has((page.pageType ?? "").toLowerCase())
  ) {
    return "Apri la scheda e lancia AI/GEO/CRO";
  }
  if (page.score != null && page.score < 60) {
    return "Apri la scheda e risolvi le priorità tecniche";
  }
  return "Apri la scheda e rivedi le azioni consigliate";
}

function _computePagePriorityScore(input: {
  page: GrowthAuditPage;
  pageFindings: GrowthAuditFinding[];
  pageTasks: GrowthAuditTask[];
  hasAiAnalysis: boolean;
  aiMeta: GrowthAuditPageAiMetadata | null;
}): number {
  const { page, pageFindings, pageTasks, hasAiAnalysis, aiMeta } = input;
  let score = _getTechnicalScoreBoost(page.score);
  score += _getBusinessPageTypeBoost(page.pageType ?? "");

  for (const finding of pageFindings) {
    if (finding.status !== "open") continue;
    score += _getFindingSeverityBoost(finding.severity);
  }

  for (const task of pageTasks) {
    if (task.status !== "open") continue;
    score += _getTaskPriorityBoost(task.priority);
  }

  if (
    isGrowthAuditPageShopifyLinked(page) &&
    (page.pageType === "product" || page.pageType === "collection")
  ) {
    score += 5;
  }

  const pageType = (page.pageType ?? "").toLowerCase();
  if (
    !hasAiAnalysis &&
    (pageType === "product" || pageType === "collection" || pageType === "landing_page")
  ) {
    score += 8;
  }

  const geoScore = aiMeta?.geoScore ?? page.geoScore;
  if (geoScore != null && geoScore < 70) score += 10;

  const croScore = aiMeta?.croScore ?? page.croScore;
  if (croScore != null && croScore < 70) score += 10;

  const adsScore = aiMeta?.adsReadinessScore;
  if (adsScore != null && adsScore < 70) score += 8;

  score += _getSearchConsolePriorityBoost(page);

  return Math.max(0, score);
}

export function buildGrowthAuditPagePriorityItems(input: {
  pages: GrowthAuditPage[];
  findings: GrowthAuditFinding[];
  tasks: GrowthAuditTask[];
  pageResultsByPageId?: Record<string, GrowthAuditPageResult[]>;
}): GrowthAuditPagePriorityItem[] {
  const { pages, findings, tasks } = input;
  const openFindings = findings.filter((f) => f.status === "open");
  const openTasks = tasks.filter((t) => t.status === "open");

  const items = pages.map((page) => {
    const pageFindings = getFindingsForPage(openFindings, page.id);
    const pageTasks = getTasksForPage(openTasks, page.id);
    const aiMeta = getGrowthAuditPageAiMetadata(page);
    const hasAiAnalysis = hasGrowthAuditPageAiAnalysis(page);

    const highPriorityFindings = pageFindings.filter(
      (f) => f.severity === "critical" || f.severity === "high",
    ).length;

    const priorityScore = _computePagePriorityScore({
      page,
      pageFindings,
      pageTasks,
      hasAiAnalysis,
      aiMeta,
    });

    const reasons = _buildPagePriorityReasons({
      page,
      pageFindings,
      openTasks: pageTasks.length,
      highPriorityFindings,
      hasAiAnalysis,
      aiMeta,
    });

    return {
      pageId: page.id,
      url: page.url,
      title: page.title || page.url,
      pageType: page.pageType,
      pageTypeLabel: getGrowthAuditPageTypeLabel(page.pageType),
      sourceLabel: getGrowthAuditPageSourceLabel(page.source),
      score: page.score ?? null,
      aiScore: aiMeta?.latestScore ?? null,
      geoScore: aiMeta?.geoScore ?? page.geoScore ?? null,
      croScore: aiMeta?.croScore ?? page.croScore ?? null,
      adsReadinessScore: aiMeta?.adsReadinessScore ?? null,
      openFindings: pageFindings.length,
      highPriorityFindings,
      openTasks: pageTasks.length,
      isShopifyLinked: isGrowthAuditPageShopifyLinked(page),
      sourceEntityType: page.sourceEntityType,
      priorityScore,
      priorityLevel: _resolvePriorityLevel(priorityScore),
      reasons,
      recommendedNextAction: _buildRecommendedNextAction({
        page,
        pageFindings,
        hasAiAnalysis,
      }),
    };
  });

  return items.sort((a, b) => {
    if (b.priorityScore !== a.priorityScore) return b.priorityScore - a.priorityScore;
    if (b.highPriorityFindings !== a.highPriorityFindings) {
      return b.highPriorityFindings - a.highPriorityFindings;
    }
    const scoreA = a.score ?? 999;
    const scoreB = b.score ?? 999;
    return scoreA - scoreB;
  });
}

export function getGrowthAuditPriorityLevelLabel(
  level: GrowthAuditPagePriorityLevel | string,
): string {
  return PRIORITY_LEVEL_LABELS[level as GrowthAuditPagePriorityLevel] ?? level;
}

export function getGrowthAuditPriorityLevelBadgeClass(
  level: GrowthAuditPagePriorityLevel | string,
): string {
  const normalized = (level || "low").toLowerCase();
  const valid = ["critical", "high", "medium", "low"].includes(normalized)
    ? normalized
    : "low";
  return `growth-audit-top-page-card growth-audit-top-page-card--${valid}`;
}

export function normalizeGrowthAuditClusterKey(input: {
  category?: string | null;
  title?: string | null;
}): string {
  return [_normalizePriorityText(input.category), _normalizePriorityText(input.title)].join("|");
}

export type GrowthAuditSiteIssueCluster = {
  key: string;
  category: string;
  title: string;
  count: number;
  severity: "critical" | "high" | "medium" | "low" | "info";
  affectedPageIds: string[];
  recommendation: string;
};

function _maxSeverity(severities: string[]): GrowthAuditSiteIssueCluster["severity"] {
  let best = 99;
  let result: GrowthAuditSiteIssueCluster["severity"] = "medium";
  for (const severity of severities) {
    const order = SEVERITY_ORDER[severity] ?? 99;
    if (order < best) {
      best = order;
      result = (severity as GrowthAuditSiteIssueCluster["severity"]) || "medium";
    }
  }
  return result;
}

function _mostFrequentRecommendation(recommendations: string[]): string {
  const counts = new Map<string, number>();
  for (const rec of recommendations) {
    const trimmed = rec.trim();
    if (!trimmed) continue;
    counts.set(trimmed, (counts.get(trimmed) ?? 0) + 1);
  }
  let best = "";
  let bestCount = 0;
  for (const [rec, count] of counts) {
    if (count > bestCount) {
      best = rec;
      bestCount = count;
    }
  }
  return best || recommendations.find((r) => r.trim()) || "Rivedi e correggi su ogni pagina interessata.";
}

export function buildGrowthAuditSiteIssueClusters(
  findings: GrowthAuditFinding[],
  tasks: GrowthAuditTask[],
): GrowthAuditSiteIssueCluster[] {
  const openFindings = findings.filter((f) => f.status === "open");
  const openTasks = tasks.filter((t) => t.status === "open");

  const findingGroups = new Map<
    string,
    {
      category: string;
      title: string;
      severities: string[];
      pageIds: Set<string>;
      recommendations: string[];
    }
  >();

  for (const finding of openFindings) {
    const key = normalizeGrowthAuditClusterKey({
      category: finding.category,
      title: finding.title,
    });
    const existing = findingGroups.get(key);
    if (existing) {
      existing.severities.push(finding.severity);
      if (finding.pageId) existing.pageIds.add(finding.pageId);
      if (finding.recommendation) existing.recommendations.push(finding.recommendation);
    } else {
      findingGroups.set(key, {
        category: finding.category,
        title: finding.title,
        severities: [finding.severity],
        pageIds: new Set(finding.pageId ? [finding.pageId] : []),
        recommendations: finding.recommendation ? [finding.recommendation] : [],
      });
    }
  }

  const clusters: GrowthAuditSiteIssueCluster[] = [...findingGroups.entries()].map(
    ([key, group]) => ({
      key,
      category: group.category,
      title: group.title,
      count: group.severities.length,
      severity: _maxSeverity(group.severities),
      affectedPageIds: [...group.pageIds],
      recommendation: _mostFrequentRecommendation(group.recommendations),
    }),
  );

  const findingTitleKeys = new Set(
    openFindings.map((f) => _normalizePriorityText(f.title)),
  );

  for (const task of openTasks) {
    const normalizedTitle = _normalizePriorityText(task.title);
    if (findingTitleKeys.has(normalizedTitle)) continue;

    const key = normalizeGrowthAuditClusterKey({ category: "task", title: task.title });
    const existing = clusters.find((c) => c.key === key);
    if (existing) {
      existing.count += 1;
      if (task.pageId && !existing.affectedPageIds.includes(task.pageId)) {
        existing.affectedPageIds.push(task.pageId);
      }
      continue;
    }
    clusters.push({
      key,
      category: "task",
      title: task.title,
      count: 1,
      severity: _maxSeverity([task.priority === "high" ? "high" : "medium"]),
      affectedPageIds: task.pageId ? [task.pageId] : [],
      recommendation: task.description?.trim() || task.title,
    });
  }

  return clusters.sort((a, b) => {
    const severityDiff = (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99);
    if (severityDiff !== 0) return severityDiff;
    return b.count - a.count;
  });
}

export type GrowthAuditAiCoverageStats = {
  totalPages: number;
  technicallyAnalyzedPages: number;
  aiAnalyzedPages: number;
  productsWithoutAi: number;
  collectionsWithoutAi: number;
  strategicWithoutAi: number;
  coveragePercent: number;
};

export function buildGrowthAuditAiCoverageStats(
  pages: GrowthAuditPage[],
  summary?: GrowthAuditRunSummary | null,
): GrowthAuditAiCoverageStats {
  const technicallyAnalyzedPages = pages.filter(
    (p) => p.status === "analyzed" || p.score != null,
  ).length;

  const aiAnalyzedPages = pages.filter((p) => hasGrowthAuditPageAiAnalysis(p)).length;

  const products = pages.filter((p) => p.pageType === "product");
  const collections = pages.filter((p) => p.pageType === "collection");
  const strategic = pages.filter((p) =>
    STRATEGIC_AI_PAGE_TYPES.has((p.pageType ?? "").toLowerCase()),
  );

  const productsWithoutAi = products.filter((p) => !hasGrowthAuditPageAiAnalysis(p)).length;
  const collectionsWithoutAi = collections.filter(
    (p) => !hasGrowthAuditPageAiAnalysis(p),
  ).length;
  const strategicWithoutAi = strategic.filter((p) => !hasGrowthAuditPageAiAnalysis(p)).length;

  const coverageBase = strategic.length > 0 ? strategic.length : pages.length;
  const coveragePercent =
    coverageBase > 0 ? Math.round((aiAnalyzedPages / coverageBase) * 100) : 0;

  return {
    totalPages: pages.length,
    technicallyAnalyzedPages,
    aiAnalyzedPages: summary?.aiPagesAnalyzed ?? aiAnalyzedPages,
    productsWithoutAi,
    collectionsWithoutAi,
    strategicWithoutAi,
    coveragePercent,
  };
}

export type GrowthAuditWorkflowStepStatus =
  | "todo"
  | "available"
  | "done"
  | "recommended";

export type GrowthAuditWorkflowStep = {
  key: string;
  label: string;
  status: GrowthAuditWorkflowStepStatus;
  anchorId?: string;
};

const STRATEGIC_WORKFLOW_PAGE_TYPES = new Set([
  "product",
  "collection",
  "landing_page",
  "homepage",
  "blog_article",
  "blog",
  "article",
]);

export function getGrowthAuditWorkspaceOperativeNote(pageType: string): string {
  const normalized = pageType.toLowerCase();
  if (normalized === "product") {
    return "Per pagine prodotto, parti da trust, CTA, immagini, meta e descrizione. Dopo ogni modifica importante, riscansiona.";
  }
  if (normalized === "collection") {
    return "Per collection, lavora su testo categoria, intent commerciale, schema e linking interno.";
  }
  if (normalized === "blog_article" || normalized === "blog" || normalized === "article") {
    return "Per articoli, lavora su intent, struttura, E-E-A-T, FAQ e linking verso prodotti.";
  }
  return "Correggi title, meta, schema e contenuti. Dopo modifiche Shopify o on-page, riscansiona la pagina per aggiornare score e problemi.";
}

export function buildGrowthAuditPageWorkflowSteps(input: {
  page: GrowthAuditPage;
  priorityActionsCount: number;
  hasAiResult: boolean;
  hasPerformanceResult?: boolean;
  hasSearchConsoleData?: boolean;
  shopifyEditable: boolean;
  openFindingsCount: number;
}): GrowthAuditWorkflowStep[] {
  const {
    page,
    priorityActionsCount,
    hasAiResult,
    hasPerformanceResult = false,
    hasSearchConsoleData = false,
    shopifyEditable,
    openFindingsCount,
  } = input;
  const isAnalyzed = page.status === "analyzed";
  const isStrategic = STRATEGIC_WORKFLOW_PAGE_TYPES.has((page.pageType ?? "").toLowerCase());
  const canRescan = page.status !== "analyzing";
  const hasScore = page.score != null;

  const priorityStatus: GrowthAuditWorkflowStepStatus =
    priorityActionsCount > 0
      ? "recommended"
      : isAnalyzed
        ? "done"
        : "available";

  const modifyStatus: GrowthAuditWorkflowStepStatus = shopifyEditable
    ? openFindingsCount > 0
      ? "recommended"
      : "available"
    : "todo";

  const aiStatus: GrowthAuditWorkflowStepStatus = hasAiResult
    ? "done"
    : isAnalyzed && isStrategic && !hasAiResult
      ? "recommended"
      : isAnalyzed
        ? "available"
        : "todo";

  const rescanStatus: GrowthAuditWorkflowStepStatus = canRescan ? "available" : "todo";

  const verifyStatus: GrowthAuditWorkflowStepStatus = hasScore
    ? page.score != null && page.score < 80
      ? "recommended"
      : "done"
    : canRescan
      ? "available"
      : "todo";

  const performanceStatus: GrowthAuditWorkflowStepStatus = hasPerformanceResult
    ? "done"
    : isStrategic || page.pageType === "product" || page.pageType === "landing"
      ? "recommended"
      : "available";

  const searchConsoleStatus: GrowthAuditWorkflowStepStatus = hasSearchConsoleData
    ? "done"
    : isAnalyzed
      ? "available"
      : "todo";

  return [
    { key: "priority", label: "Priorità", status: priorityStatus, anchorId: "priority-actions" },
    { key: "edit", label: "Modifica", status: modifyStatus, anchorId: "shopify-edit" },
    { key: "performance", label: "Performance", status: performanceStatus, anchorId: "performance" },
    {
      key: "search-console",
      label: "Search Console",
      status: searchConsoleStatus,
      anchorId: "search-console",
    },
    { key: "ai", label: "Analisi AI", status: aiStatus, anchorId: "ai-geo-cro" },
    { key: "rescan", label: "Rescan", status: rescanStatus },
    { key: "verify", label: "Verifica", status: verifyStatus, anchorId: "technical-data" },
  ];
}

export function getGrowthAuditWorkflowStepStatusLabel(
  status: GrowthAuditWorkflowStepStatus,
): string {
  const labels: Record<GrowthAuditWorkflowStepStatus, string> = {
    todo: "Da fare",
    available: "Disponibile",
    done: "Completato",
    recommended: "Consigliato",
  };
  return labels[status];
}
