import type {
  GrowthAuditFinding,
  GrowthAuditInventoryCounts,
  GrowthAuditInventoryFilter,
  GrowthAuditPage,
  GrowthAuditPageAiMetadata,
  GrowthAuditPagePerformanceMetadata,
  GrowthAuditPageSearchConsoleMetadata,
  GrowthAuditPageAnalyticsMetadata,
  GrowthAuditPageShopifyCommerceMetadata,
  GrowthAuditPageGa4EcommerceMetadata,
  GrowthAuditRunShopifyCommerceSummary,
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

export function getGrowthAuditPageAnalyticsMetadata(
  page: GrowthAuditPage,
): GrowthAuditPageAnalyticsMetadata | null {
  const analytics = page.metadata?.analytics;
  if (!analytics || typeof analytics !== "object") return null;
  return analytics as GrowthAuditPageAnalyticsMetadata;
}

export function hasGrowthAuditPageAnalyticsData(page: GrowthAuditPage): boolean {
  const meta = getGrowthAuditPageAnalyticsMetadata(page);
  return Boolean(meta && ((meta.sessions ?? 0) > 0 || (meta.totalUsers ?? 0) > 0));
}

export function getGrowthAuditPageShopifyCommerceMetadata(
  page: GrowthAuditPage,
): GrowthAuditPageShopifyCommerceMetadata | null {
  const commerce = page.metadata?.shopifyCommerce;
  if (!commerce || typeof commerce !== "object") return null;
  return commerce as GrowthAuditPageShopifyCommerceMetadata;
}

export function hasGrowthAuditPageShopifyCommerceData(page: GrowthAuditPage): boolean {
  const meta = getGrowthAuditPageShopifyCommerceMetadata(page);
  return Boolean(meta?.syncedAt);
}

export function getGrowthAuditPageGa4EcommerceMetadata(
  page: GrowthAuditPage,
): GrowthAuditPageGa4EcommerceMetadata | null {
  const funnel = page.metadata?.ga4Ecommerce;
  if (!funnel || typeof funnel !== "object") return null;
  return funnel as GrowthAuditPageGa4EcommerceMetadata;
}

export function hasGrowthAuditPageGa4EcommerceData(page: GrowthAuditPage): boolean {
  const meta = getGrowthAuditPageGa4EcommerceMetadata(page);
  return Boolean(meta?.syncedAt);
}

function _getAnalyticsPriorityBoost(page: GrowthAuditPage): number {
  const meta = getGrowthAuditPageAnalyticsMetadata(page);
  if (!meta) return 0;

  let boost = 0;
  const sessions = meta.sessions ?? 0;
  const engagementRate = meta.engagementRate ?? 0;
  const conversions = meta.conversions ?? 0;
  const revenue = meta.revenue ?? 0;
  const pageType = (page.pageType ?? "").toLowerCase();

  if (sessions >= 50 && engagementRate < 0.4) boost += 10;
  if (sessions >= 30 && conversions === 0) boost += 10;
  if (pageType === "product" && sessions >= 30 && conversions === 0) boost += 8;
  if (revenue >= 100 || sessions >= 100) boost += 6;

  return Math.min(boost, 25);
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
    {
      label: "Sessioni",
      value:
        summary?.analytics?.totalSessions != null
          ? String(summary.analytics.totalSessions)
          : "—",
    },
    {
      label: "Utenti",
      value:
        summary?.analytics?.totalUsers != null
          ? String(summary.analytics.totalUsers)
          : "—",
    },
    {
      label: "Engagement rate medio",
      value:
        summary?.analytics?.averageEngagementRate != null
          ? `${(summary.analytics.averageEngagementRate * 100).toFixed(2)}%`
          : "—",
    },
    {
      label: "Conversioni",
      value:
        summary?.analytics?.totalConversions != null
          ? String(summary.analytics.totalConversions)
          : "—",
    },
    {
      label: "Revenue",
      value:
        summary?.analytics?.totalRevenue != null
          ? summary.analytics.totalRevenue.toFixed(2)
          : "—",
    },
    {
      label: "Pagine con dati GA4",
      value:
        summary?.analytics?.pagesWithData != null
          ? String(summary.analytics.pagesWithData)
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

  const analyticsMeta = getGrowthAuditPageAnalyticsMetadata(page);
  if (analyticsMeta) {
    const sessions = analyticsMeta.sessions ?? 0;
    const engagementRate = analyticsMeta.engagementRate ?? 0;
    const conversions = analyticsMeta.conversions ?? 0;
    if (sessions >= 50 && engagementRate < 0.4) {
      reasons.push("Engagement GA4 basso con traffico significativo");
    }
    if (sessions >= 30 && conversions === 0) {
      reasons.push("Traffico GA4 senza conversioni");
    }
    if ((analyticsMeta.revenue ?? 0) >= 100 || sessions >= 100) {
      reasons.push("Alta priorità business da GA4");
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
  score += _getAnalyticsPriorityBoost(page);

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
  hasAnalyticsData?: boolean;
  hasShopifyCommerceData?: boolean;
  hasGa4EcommerceData?: boolean;
  shopifyEditable: boolean;
  openFindingsCount: number;
}): GrowthAuditWorkflowStep[] {
  const {
    page,
    priorityActionsCount,
    hasAiResult,
    hasPerformanceResult = false,
    hasSearchConsoleData = false,
    hasAnalyticsData = false,
    hasShopifyCommerceData = false,
    hasGa4EcommerceData = false,
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

  const analyticsStatus: GrowthAuditWorkflowStepStatus = hasAnalyticsData
    ? "done"
    : isAnalyzed
      ? "available"
      : "todo";

  const isProductPage = isGrowthAuditProductPage(page);

  const ga4EcommerceStatus: GrowthAuditWorkflowStepStatus = hasGa4EcommerceData
    ? "done"
    : isProductPage
      ? "available"
      : "todo";

  const commerceStatus: GrowthAuditWorkflowStepStatus = hasShopifyCommerceData
    ? "done"
    : isProductPage
      ? "available"
      : "todo";

  const workflowSteps: GrowthAuditWorkflowStep[] = [
    {
      key: "priority",
      label: isProductPage ? "Valuta priorità" : "Priorità",
      status: priorityStatus,
      anchorId: isProductPage ? "product-intelligence" : "priority-actions",
    },
    { key: "edit", label: "Modifica", status: modifyStatus, anchorId: "shopify-edit" },
  ];

  if (isProductPage) {
    workflowSteps.push({
      key: "shopify-commerce",
      label: "Shopify Commerce",
      status: commerceStatus,
      anchorId: "shopify-commerce",
    });
  }

  workflowSteps.push(
    { key: "performance", label: "Performance", status: performanceStatus, anchorId: "performance" },
    {
      key: "search-console",
      label: "Search Console",
      status: searchConsoleStatus,
      anchorId: "search-console",
    },
    {
      key: "analytics",
      label: "GA4",
      status: analyticsStatus,
      anchorId: "analytics",
    },
  );

  if (isProductPage) {
    workflowSteps.push({
      key: "ga4-ecommerce",
      label: "GA4 Funnel",
      status: ga4EcommerceStatus,
      anchorId: "ga4-ecommerce-funnel",
    });
  }

  workflowSteps.push(
    { key: "ai", label: "Analisi AI", status: aiStatus, anchorId: "ai-geo-cro" },
    { key: "rescan", label: "Rescan", status: rescanStatus },
    { key: "verify", label: "Verifica", status: verifyStatus, anchorId: "technical-data" },
  );

  return workflowSteps;
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

export type GrowthAuditProductIntelligenceLevel =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "monitor";

export type GrowthAuditProductIntelligenceSignal = {
  key: string;
  label: string;
  value: string;
  tone: "good" | "warning" | "danger" | "neutral";
  explanation: string;
};

export type GrowthAuditProductIntelligenceAction = {
  title: string;
  reason: string;
  expectedImpact: string;
  whereToFix: string;
  howToValidate: string;
};

export type GrowthAuditProductIntelligenceSummary = {
  available: boolean;
  level: GrowthAuditProductIntelligenceLevel;
  score: number;
  title: string;
  verdict: string;
  mainReason: string;
  evidence: GrowthAuditProductIntelligenceSignal[];
  missingData: string[];
  recommendedActions: GrowthAuditProductIntelligenceAction[];
};

const PRODUCT_INTELLIGENCE_LEVEL_LABELS: Record<GrowthAuditProductIntelligenceLevel, string> = {
  critical: "Priorità massima",
  high: "Priorità alta",
  medium: "Priorità media",
  low: "Priorità bassa",
  monitor: "Monitoraggio",
};

const CWV_LCP_NEEDS_IMPROVEMENT_MS = 2500;
const CWV_CLS_NEEDS_IMPROVEMENT = 0.1;
const CWV_INP_NEEDS_IMPROVEMENT_MS = 200;

export function isGrowthAuditProductPage(page: GrowthAuditPage): boolean {
  return page.pageType === "product" || page.sourceEntityType === "shopify_product";
}

export function getGrowthAuditProductIntelligenceLevelLabel(
  level: GrowthAuditProductIntelligenceLevel,
): string {
  return PRODUCT_INTELLIGENCE_LEVEL_LABELS[level];
}

export function getGrowthAuditProductIntelligenceLevelBadgeClass(
  level: GrowthAuditProductIntelligenceLevel,
): string {
  return `growth-audit-product-intelligence__priority-badge growth-audit-product-intelligence__priority-badge--${level}`;
}

function _getLatestCompletedPageResult(
  results: GrowthAuditPageResult[] | undefined,
): GrowthAuditPageResult | null {
  const completed = (results ?? []).filter((result) => result.status === "completed");
  if (completed.length === 0) return null;
  return completed.sort((a, b) => {
    const aTime = a.completedAt ?? a.createdAt ?? "";
    const bTime = b.completedAt ?? b.createdAt ?? "";
    return bTime.localeCompare(aTime);
  })[0];
}

type PerformanceArtifactsSnapshot = {
  performanceScore: number | null;
  lcp: number | null;
  cls: number | null;
  inp: number | null;
};

function _getProductIntelligencePerformanceSnapshot(
  page: GrowthAuditPage,
  performanceResults?: GrowthAuditPageResult[],
): PerformanceArtifactsSnapshot {
  const performanceMeta = getGrowthAuditPagePerformanceMetadata(page);
  const latestResult = _getLatestCompletedPageResult(performanceResults);
  const artifacts = latestResult?.artifacts as
    | {
        pagespeed?: { performanceScore?: number | null; lcp?: number | null; cls?: number | null };
        crux?: {
          lcpP75?: number | null;
          clsP75?: number | null;
          inpP75?: number | null;
        };
      }
    | undefined;
  const pagespeed = artifacts?.pagespeed;
  const crux = artifacts?.crux;

  const performanceScore =
    performanceMeta?.latestScore ??
    page.performanceScore ??
    latestResult?.score ??
    pagespeed?.performanceScore ??
    null;

  const lcp = crux?.lcpP75 ?? performanceMeta?.lcp ?? pagespeed?.lcp ?? null;
  const cls = crux?.clsP75 ?? performanceMeta?.cls ?? pagespeed?.cls ?? null;
  const inp = crux?.inpP75 ?? performanceMeta?.inp ?? null;

  return { performanceScore, lcp, cls, inp };
}

function _isPoorLcp(value: number | null): boolean {
  return value != null && value > CWV_LCP_NEEDS_IMPROVEMENT_MS;
}

function _isPoorCls(value: number | null): boolean {
  return value != null && value > CWV_CLS_NEEDS_IMPROVEMENT;
}

function _isPoorInp(value: number | null): boolean {
  return value != null && value > CWV_INP_NEEDS_IMPROVEMENT_MS;
}

function _scoreToProductIntelligenceLevel(
  score: number,
): GrowthAuditProductIntelligenceLevel {
  if (score >= 80) return "critical";
  if (score >= 60) return "high";
  if (score >= 35) return "medium";
  if (score >= 15) return "low";
  return "monitor";
}

function _hasProductIntelligenceAiData(
  page: GrowthAuditPage,
  aiResults?: GrowthAuditPageResult[],
): boolean {
  if (hasGrowthAuditPageAiAnalysis(page)) return true;
  if (aiResults?.some((result) => result.status === "completed")) return true;
  const aiMeta = getGrowthAuditPageAiMetadata(page);
  return (
    aiMeta?.latestScore != null ||
    aiMeta?.croScore != null ||
    aiMeta?.geoScore != null ||
    aiMeta?.adsReadinessScore != null ||
    page.croScore != null ||
    page.geoScore != null
  );
}

function _hasProductIntelligencePerformanceData(
  page: GrowthAuditPage,
  performanceResults?: GrowthAuditPageResult[],
): boolean {
  if (hasGrowthAuditPagePerformanceAnalysis(page)) return true;
  return _getLatestCompletedPageResult(performanceResults) != null;
}

function _buildProductIntelligenceMissingData(
  page: GrowthAuditPage,
  aiResults?: GrowthAuditPageResult[],
  performanceResults?: GrowthAuditPageResult[],
): string[] {
  const missing: string[] = [];
  if (!hasGrowthAuditPageSearchConsoleData(page)) missing.push("Search Console");
  if (!hasGrowthAuditPageAnalyticsData(page)) missing.push("GA4");
  if (!_hasProductIntelligencePerformanceData(page, performanceResults)) {
    missing.push("Performance");
  }
  if (!_hasProductIntelligenceAiData(page, aiResults)) missing.push("AI/GEO/CRO");
  if (page.sourceEntityType !== "shopify_product") missing.push("Shopify product link");
  if (isGrowthAuditProductPage(page) && !hasGrowthAuditPageShopifyCommerceData(page)) {
    missing.push("Shopify Commerce");
  }
  if (isGrowthAuditProductPage(page) && !hasGrowthAuditPageGa4EcommerceData(page)) {
    missing.push("GA4 Ecommerce Funnel");
  }
  return missing;
}

type ProductIntelligenceTheme =
  | "gsc_ctr"
  | "gsc_position"
  | "ga4_conversion"
  | "performance"
  | "cro_ai"
  | "shopify_commerce"
  | "shopify_stock"
  | "ga4_ecommerce_funnel"
  | "incomplete_data"
  | "general";

type ProductIntelligenceScoreContext = {
  score: number;
  themes: Partial<Record<ProductIntelligenceTheme, number>>;
  gscMeta: GrowthAuditPageSearchConsoleMetadata | null;
  analyticsMeta: GrowthAuditPageAnalyticsMetadata | null;
  commerceMeta: GrowthAuditPageShopifyCommerceMetadata | null;
  ga4EcommerceMeta: GrowthAuditPageGa4EcommerceMetadata | null;
  performanceSnapshot: PerformanceArtifactsSnapshot;
  croScore: number | null;
  geoScore: number | null;
  adsScore: number | null;
  aiLatestScore: number | null;
  openFindings: GrowthAuditFinding[];
};

function _isTopCommerceProduct(
  _page: GrowthAuditPage,
  commerceMeta: GrowthAuditPageShopifyCommerceMetadata | null,
  runSummary?: GrowthAuditRunShopifyCommerceSummary | null,
): boolean {
  const sales = commerceMeta?.sales ?? 0;
  if (sales <= 0) return false;
  const topProducts = runSummary?.topProducts ?? [];
  if (topProducts.length === 0) {
    return sales >= 100;
  }
  const thresholdIndex = Math.max(0, Math.ceil(topProducts.length * 0.2) - 1);
  const thresholdSales = topProducts[thresholdIndex]?.sales ?? 0;
  return sales >= thresholdSales;
}

function _computeProductPriorityScore(input: {
  page: GrowthAuditPage;
  findings: GrowthAuditFinding[];
  tasks: GrowthAuditTask[];
  performanceResults?: GrowthAuditPageResult[];
  runSummary?: GrowthAuditRunShopifyCommerceSummary | null;
}): ProductIntelligenceScoreContext {
  const { page, findings, tasks, performanceResults, runSummary } = input;
  const themes: Partial<Record<ProductIntelligenceTheme, number>> = {};
  const addTheme = (theme: ProductIntelligenceTheme, points: number) => {
    themes[theme] = (themes[theme] ?? 0) + points;
  };

  let score = 0;
  const gscMeta = getGrowthAuditPageSearchConsoleMetadata(page);
  const analyticsMeta = getGrowthAuditPageAnalyticsMetadata(page);
  const commerceMeta = getGrowthAuditPageShopifyCommerceMetadata(page);
  const ga4EcommerceMeta = getGrowthAuditPageGa4EcommerceMetadata(page);
  const aiMeta = getGrowthAuditPageAiMetadata(page);
  const performanceSnapshot = _getProductIntelligencePerformanceSnapshot(page, performanceResults);

  if (gscMeta) {
    const impressions = gscMeta.impressions ?? 0;
    const ctr = gscMeta.ctr ?? 0;
    const position = gscMeta.position ?? 0;

    if (impressions > 1000) {
      score += 20;
      addTheme("gsc_ctr", 20);
    } else if (impressions >= 200) {
      score += 12;
      addTheme("gsc_ctr", 12);
    }

    if (impressions > 200 && ctr < 0.01) {
      score += 18;
      addTheme("gsc_ctr", 18);
    } else if (impressions > 200 && ctr < 0.02) {
      score += 10;
      addTheme("gsc_ctr", 10);
    }

    if (position >= 4 && position <= 15) {
      score += 15;
      addTheme("gsc_position", 15);
    }

    if ((gscMeta.topQueries?.length ?? 0) > 0) {
      score += 5;
      addTheme("gsc_position", 5);
    }
  }

  if (analyticsMeta) {
    const sessions = analyticsMeta.sessions ?? 0;
    const engagementRate = analyticsMeta.engagementRate ?? 0;
    const conversions = analyticsMeta.conversions ?? 0;
    const revenue = analyticsMeta.revenue;

    if (sessions > 300) {
      score += 18;
      addTheme("ga4_conversion", 18);
    } else if (sessions >= 50) {
      score += 10;
      addTheme("ga4_conversion", 10);
    }

    if (engagementRate < 0.45 && sessions > 50) {
      score += 12;
      addTheme("ga4_conversion", 12);
    }

    if (conversions === 0 && sessions > 50) {
      score += 15;
      addTheme("ga4_conversion", 15);
    }

    if (revenue != null) {
      if (revenue > 0) {
        score += 10;
        addTheme("ga4_conversion", 10);
      }
      if (revenue >= 100) {
        score += 15;
        addTheme("ga4_conversion", 15);
      }
    }
  }

  const perfScore = performanceSnapshot.performanceScore;
  if (perfScore != null) {
    if (perfScore < 50) {
      score += 12;
      addTheme("performance", 12);
    } else if (perfScore < 80) {
      score += 7;
      addTheme("performance", 7);
    }
  }

  if (_isPoorLcp(performanceSnapshot.lcp)) {
    score += 8;
    addTheme("performance", 8);
  }
  if (_isPoorCls(performanceSnapshot.cls)) {
    score += 8;
    addTheme("performance", 8);
  }
  if (_isPoorInp(performanceSnapshot.inp)) {
    score += 8;
    addTheme("performance", 8);
  }

  const croScore = aiMeta?.croScore ?? page.croScore ?? null;
  const geoScore = aiMeta?.geoScore ?? page.geoScore ?? null;
  const adsScore = aiMeta?.adsReadinessScore ?? null;
  const aiLatestScore = aiMeta?.latestScore ?? null;

  if (croScore != null && croScore < 70) {
    score += 12;
    addTheme("cro_ai", 12);
  }
  if (geoScore != null && geoScore < 70) {
    score += 8;
    addTheme("cro_ai", 8);
  }
  if (adsScore != null && adsScore < 70) {
    score += 8;
    addTheme("cro_ai", 8);
  }
  if (aiLatestScore != null && aiLatestScore < 70) {
    score += 10;
    addTheme("cro_ai", 10);
  }

  const openFindings = findings.filter((finding) => finding.status === "open");
  const openTasks = tasks.filter((task) => task.status === "open");

  for (const finding of openFindings) {
    if (finding.severity === "critical") score += 15;
    else if (finding.severity === "high") score += 8;
  }

  for (const task of openTasks) {
    if (task.priority === "high") score += 6;
  }

  if (page.sourceEntityType === "shopify_product") {
    score += 5;
  }

  if (commerceMeta) {
    const sales = commerceMeta.sales ?? 0;
    const quantitySold = commerceMeta.quantitySold ?? 0;
    const ordersCount = commerceMeta.ordersCount ?? 0;
    const stock = commerceMeta.stock;
    const availableForSale = commerceMeta.availableForSale;
    const impressions = gscMeta?.impressions ?? 0;
    const sessions = analyticsMeta?.sessions ?? 0;

    if (sales > 0) {
      score += 15;
      addTheme("shopify_commerce", 15);
    }
    if (_isTopCommerceProduct(page, commerceMeta, runSummary)) {
      score += 20;
      addTheme("shopify_commerce", 20);
    }
    if (quantitySold > 0) {
      score += 10;
      addTheme("shopify_commerce", 10);
    }
    if (ordersCount > 0) {
      score += 8;
      addTheme("shopify_commerce", 8);
    }

    const hasDemandSignal = sales > 0 || impressions > 200 || sessions > 50;
    if (hasDemandSignal && (stock != null && stock <= 0 || availableForSale === false)) {
      score += 15;
      addTheme("shopify_stock", 15);
    } else if (
      sales > 0 &&
      stock != null &&
      stock > 0 &&
      stock <= 10
    ) {
      score += 10;
      addTheme("shopify_stock", 10);
    }

    if (
      availableForSale === true &&
      ((impressions > 200 && (gscMeta?.ctr ?? 0) < 0.02) || (sessions > 50 && (analyticsMeta?.conversions ?? 0) === 0))
    ) {
      score += 5;
      addTheme("shopify_commerce", 5);
    }
  }

  if (ga4EcommerceMeta) {
    const itemViews = ga4EcommerceMeta.itemViews ?? ga4EcommerceMeta.itemViewEvents ?? 0;
    const itemsAddedToCart = ga4EcommerceMeta.itemsAddedToCart ?? 0;
    const itemsCheckedOut = ga4EcommerceMeta.itemsCheckedOut ?? 0;
    const itemsPurchased = ga4EcommerceMeta.itemsPurchased ?? 0;
    const itemRevenue = ga4EcommerceMeta.itemRevenue ?? 0;
    const viewToCartRate = ga4EcommerceMeta.viewToCartRate ?? 0;
    const cartToPurchaseRate = ga4EcommerceMeta.cartToPurchaseRate ?? 0;

    if (itemViews > 100) {
      score += 15;
      addTheme("ga4_ecommerce_funnel", 15);
    } else if (itemViews >= 30) {
      score += 8;
      addTheme("ga4_ecommerce_funnel", 8);
    }
    if (itemViews > 50 && itemsAddedToCart === 0) {
      score += 18;
      addTheme("ga4_ecommerce_funnel", 18);
    }
    if (itemsAddedToCart > 0 && itemsPurchased === 0) {
      score += 15;
      addTheme("ga4_ecommerce_funnel", 15);
    }
    if (itemsCheckedOut > 0 && itemsPurchased === 0) {
      score += 12;
      addTheme("ga4_ecommerce_funnel", 12);
    }
    if (itemsPurchased > 0) {
      score += 12;
      addTheme("ga4_ecommerce_funnel", 12);
    }
    if (itemRevenue > 0) {
      score += 12;
      addTheme("ga4_ecommerce_funnel", 12);
    }
    if (viewToCartRate < 0.05 && itemViews > 50) {
      score += 12;
      addTheme("ga4_ecommerce_funnel", 12);
    }
    if (cartToPurchaseRate < 0.2 && itemsAddedToCart > 5) {
      score += 10;
      addTheme("ga4_ecommerce_funnel", 10);
    }
  }

  return {
    score: Math.min(100, Math.max(0, score)),
    themes,
    gscMeta,
    analyticsMeta,
    commerceMeta,
    ga4EcommerceMeta,
    performanceSnapshot,
    croScore,
    geoScore,
    adsScore,
    aiLatestScore,
    openFindings,
  };
}

function _getDominantProductIntelligenceTheme(
  themes: Partial<Record<ProductIntelligenceTheme, number>>,
): ProductIntelligenceTheme {
  const entries = Object.entries(themes) as [ProductIntelligenceTheme, number][];
  if (entries.length === 0) return "general";
  entries.sort((a, b) => b[1] - a[1]);
  return entries[0][0];
}

function _buildProductIntelligenceVerdict(input: {
  context: ProductIntelligenceScoreContext;
  missingData: string[];
}): { title: string; verdict: string; mainReason: string } {
  const { context, missingData } = input;
  const { gscMeta, analyticsMeta, commerceMeta, ga4EcommerceMeta, performanceSnapshot, croScore, aiLatestScore, themes, openFindings } = context;

  const dominant = _getDominantProductIntelligenceTheme(themes);
  const dominantWeight = themes[dominant] ?? 0;
  const hasStrongSignal = dominantWeight >= 15;

  const impressions = gscMeta?.impressions ?? 0;
  const ctr = gscMeta?.ctr ?? 0;
  const position = gscMeta?.position ?? 0;
  const sessions = analyticsMeta?.sessions ?? 0;
  const conversions = analyticsMeta?.conversions ?? 0;
  const perfScore = performanceSnapshot.performanceScore;
  const sales = commerceMeta?.sales ?? 0;
  const stock = commerceMeta?.stock;
  const availableForSale = commerceMeta?.availableForSale;
  const hasCriticalFindings = openFindings.some(
    (finding) => finding.severity === "critical" || finding.severity === "high",
  );

  if (
    ga4EcommerceMeta &&
    ga4EcommerceMeta.matchedBy === "none" &&
    (impressions > 200 || sessions > 50 || sales > 0)
  ) {
    return {
      title: "Tracking ecommerce GA4 da verificare",
      verdict:
        "Il prodotto ha segnali di domanda ma GA4 non ha abbinato dati item-level in modo affidabile.",
      mainReason: "Possibile mismatch item_id/SKU o tracking ecommerce incompleto.",
    };
  }

  const funnelViews = ga4EcommerceMeta?.itemViews ?? ga4EcommerceMeta?.itemViewEvents ?? 0;
  const funnelCart = ga4EcommerceMeta?.itemsAddedToCart ?? 0;
  const funnelPurchases = ga4EcommerceMeta?.itemsPurchased ?? 0;

  if (ga4EcommerceMeta && funnelViews > 50 && funnelCart === 0) {
    return {
      title: "View item alte ma add to cart assenti",
      verdict:
        "GA4 mostra visualizzazioni prodotto ma pochi o zero add to cart nel periodo.",
      mainReason: "Frizione su offerta, prezzo, trust, immagini o CTA.",
    };
  }

  if (ga4EcommerceMeta && funnelCart > 0 && funnelPurchases === 0) {
    return {
      title: "Carrello attivo ma acquisti assenti",
      verdict:
        "GA4 mostra add to cart ma pochi acquisti: possibile frizione tra carrello e checkout.",
      mainReason: "Verifica spedizione, costi finali, trust e checkout.",
    };
  }

  if (ga4EcommerceMeta && funnelPurchases > 0) {
    return {
      title: "Funnel GA4 che monetizza",
      verdict:
        "GA4 mostra acquisti item-level. Le ottimizzazioni possono amplificare un prodotto già validato.",
      mainReason: "Purchase o item revenue presenti nel funnel GA4.",
    };
  }

  if (
    dominant === "shopify_stock" ||
    ((sales > 0 || impressions > 200 || sessions > 50) &&
      (stock != null && stock <= 0 || availableForSale === false))
  ) {
    return {
      title: "Disponibilità da risolvere prima di spingere traffico",
      verdict:
        "Il prodotto ha segnali di domanda o vendite, ma stock o disponibilità possono limitare le conversioni.",
      mainReason: "Inventario insufficiente rispetto alla domanda rilevata.",
    };
  }

  if (
    sales > 0 &&
    hasCriticalFindings &&
    (dominant === "shopify_commerce" || themes.shopify_commerce != null)
  ) {
    return {
      title: "Prodotto che monetizza: priorità alta",
      verdict:
        "Shopify mostra vendite nel periodo. Vale la pena intervenire subito su SEO, CRO e performance per amplificare un prodotto già validato.",
      mainReason: "Revenue Shopify presente con criticità aperte sulla pagina.",
    };
  }

  if (
    commerceMeta &&
    (impressions > 200 || sessions > 50) &&
    sales === 0 &&
    (commerceMeta.quantitySold ?? 0) === 0
  ) {
    return {
      title: "Potenziale non monetizzato",
      verdict:
        "La pagina riceve segnali di domanda organica o traffico, ma Shopify non mostra vendite nel periodo.",
      mainReason: "Traffico o visibilità senza conversione ecommerce.",
    };
  }

  if (
    dominant === "gsc_ctr" ||
    (impressions > 200 && ctr < 0.01)
  ) {
    return {
      title: "Pagina con visibilità organica da sfruttare meglio",
      verdict:
        "La pagina riceve impression da Google ma il CTR è basso. Prima priorità: migliorare snippet, title/meta e allineamento con le query principali.",
      mainReason: "Visibilità organica alta ma pochi click rispetto alle impression.",
    };
  }

  if (
    dominant === "ga4_conversion" ||
    (sessions > 50 && conversions === 0)
  ) {
    return {
      title: "Pagina con traffico ma conversione debole",
      verdict:
        "La pagina riceve traffico ma non trasforma abbastanza. Prima priorità: CRO, trust, CTA, immagini e chiarezza dell'offerta.",
      mainReason: "Traffico GA4 presente senza conversioni sufficienti.",
    };
  }

  if (
    dominant === "performance" ||
    (perfScore != null && perfScore < 50) ||
    _isPoorLcp(performanceSnapshot.lcp) ||
    _isPoorCls(performanceSnapshot.cls) ||
    _isPoorInp(performanceSnapshot.inp)
  ) {
    return {
      title: "Pagina da alleggerire prima di spingere traffico",
      verdict:
        "La performance può limitare esperienza utente e conversioni, soprattutto mobile.",
      mainReason: "Velocità o Core Web Vitals sotto soglia.",
    };
  }

  if (
    dominant === "cro_ai" ||
    (croScore != null && croScore < 70) ||
    (aiLatestScore != null && aiLatestScore < 70)
  ) {
    return {
      title: "Pagina persuasiva da rinforzare",
      verdict:
        "L'analisi AI/CRO indica debolezze su fiducia, CTA o completezza del contenuto.",
      mainReason: "Score persuasivo o AI sotto soglia.",
    };
  }

  if (dominant === "gsc_position" || (position >= 4 && position <= 15 && impressions >= 200)) {
    return {
      title: "Pagina vicina a posizioni più redditizie",
      verdict:
        "La pagina è nelle vicinanze della prima pagina Google. Prima priorità: rafforzare contenuto e FAQ sulle query principali.",
      mainReason: "Posizione media tra 4 e 15 con impression significative.",
    };
  }

  if (missingData.length >= 3 && !hasStrongSignal) {
    return {
      title: "Dati ancora incompleti",
      verdict:
        "La pagina è collegata, ma mancano dati sufficienti per una priorità forte. Completa GSC, GA4, Performance e AI/GEO/CRO.",
      mainReason: "Priorità meno affidabile finché mancano analisi chiave.",
    };
  }

  return {
    title: "Pagina prodotto da monitorare",
    verdict:
      "Non emergono urgenze forti, ma conviene tenere sotto controllo organico, analytics e performance.",
    mainReason: "Segnali misti senza un tema dominante critico.",
  };
}

function _formatItalianNumber(value: number): string {
  return value.toLocaleString("it-IT");
}

function _formatItalianPercent(value: number): string {
  return `${(value * 100).toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
}

function _buildProductIntelligenceEvidence(input: {
  context: ProductIntelligenceScoreContext;
  priorityActionsCount: number;
}): GrowthAuditProductIntelligenceSignal[] {
  const { context, priorityActionsCount } = input;
  const signals: GrowthAuditProductIntelligenceSignal[] = [];
  const { gscMeta, analyticsMeta, commerceMeta, ga4EcommerceMeta, performanceSnapshot, croScore, openFindings } = context;

  if (ga4EcommerceMeta) {
    const itemViews = ga4EcommerceMeta.itemViews ?? ga4EcommerceMeta.itemViewEvents ?? 0;
    if (itemViews > 0) {
      signals.push({
        key: "ga4-item-views",
        label: "View item",
        value: _formatItalianNumber(itemViews),
        tone: itemViews > 100 ? "warning" : "neutral",
        explanation: "Visualizzazioni prodotto item-level in GA4.",
      });
    }
    if (ga4EcommerceMeta.itemsAddedToCart != null) {
      signals.push({
        key: "ga4-add-to-cart",
        label: "Add to cart",
        value: _formatItalianNumber(ga4EcommerceMeta.itemsAddedToCart),
        tone:
          itemViews > 50 && ga4EcommerceMeta.itemsAddedToCart === 0
            ? "danger"
            : ga4EcommerceMeta.itemsAddedToCart > 0
              ? "good"
              : "neutral",
        explanation: "Aggiunte al carrello item-level in GA4.",
      });
    }
    if (ga4EcommerceMeta.itemsCheckedOut != null) {
      signals.push({
        key: "ga4-checkout",
        label: "Checkout",
        value: _formatItalianNumber(ga4EcommerceMeta.itemsCheckedOut),
        tone: ga4EcommerceMeta.itemsCheckedOut > 0 ? "good" : "neutral",
        explanation: "Inizi checkout item-level in GA4.",
      });
    }
    if (ga4EcommerceMeta.itemsPurchased != null) {
      signals.push({
        key: "ga4-purchase",
        label: "Purchase",
        value: _formatItalianNumber(ga4EcommerceMeta.itemsPurchased),
        tone: ga4EcommerceMeta.itemsPurchased > 0 ? "good" : "warning",
        explanation: "Acquisti item-level in GA4.",
      });
    }
    if (ga4EcommerceMeta.itemRevenue != null && ga4EcommerceMeta.itemRevenue > 0) {
      const currency = ga4EcommerceMeta.currency ? ` ${ga4EcommerceMeta.currency}` : "";
      signals.push({
        key: "ga4-item-revenue",
        label: "Item revenue",
        value:
          ga4EcommerceMeta.itemRevenue.toLocaleString("it-IT", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }) + currency,
        tone: "good",
        explanation: "Ricavo item-level attribuito in GA4.",
      });
    }
    if (ga4EcommerceMeta.viewToCartRate != null) {
      signals.push({
        key: "ga4-view-to-cart",
        label: "View → cart rate",
        value: _formatItalianPercent(ga4EcommerceMeta.viewToCartRate),
        tone:
          ga4EcommerceMeta.viewToCartRate < 0.05 && itemViews > 50
            ? "danger"
            : "neutral",
        explanation: "Tasso conversione da view a carrello.",
      });
    }
    if (ga4EcommerceMeta.cartToPurchaseRate != null) {
      signals.push({
        key: "ga4-cart-to-purchase",
        label: "Cart → purchase rate",
        value: _formatItalianPercent(ga4EcommerceMeta.cartToPurchaseRate),
        tone:
          ga4EcommerceMeta.cartToPurchaseRate < 0.2 &&
          (ga4EcommerceMeta.itemsAddedToCart ?? 0) > 5
            ? "warning"
            : "neutral",
        explanation: "Tasso conversione da carrello ad acquisto.",
      });
    }

    const matchedVariants = (ga4EcommerceMeta.variantBreakdown ?? []).filter(
      (variant) => variant.matchedBy && variant.matchedBy !== "none",
    );
    if (matchedVariants.length > 0) {
      signals.push({
        key: "ga4-variants-with-funnel",
        label: "Varianti con funnel",
        value: _formatItalianNumber(matchedVariants.length),
        tone: "good",
        explanation: "Varianti con metriche GA4 abbinate in modo deterministico.",
      });

      const bestRevenueVariant = matchedVariants.find(
        (variant) => variant.variantLegacyId === ga4EcommerceMeta.bestVariantByRevenue,
      );
      if (bestRevenueVariant) {
        const currency = ga4EcommerceMeta.currency ? ` ${ga4EcommerceMeta.currency}` : "";
        signals.push({
          key: "ga4-best-variant-revenue",
          label: "Migliore variante per revenue",
          value: `${bestRevenueVariant.variantTitle || bestRevenueVariant.variantLegacyId || "—"} · ${(bestRevenueVariant.itemRevenue ?? 0).toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}${currency}`,
          tone: "good",
          explanation: "Variante con item revenue più alta nel periodo.",
        });
      }

      const bestPurchaseVariant = matchedVariants.find(
        (variant) => variant.variantLegacyId === ga4EcommerceMeta.bestVariantByPurchase,
      );
      if (bestPurchaseVariant) {
        signals.push({
          key: "ga4-best-variant-purchase",
          label: "Migliore variante per purchase",
          value: `${bestPurchaseVariant.variantTitle || bestPurchaseVariant.variantLegacyId || "—"} · ${_formatItalianNumber(bestPurchaseVariant.itemsPurchased ?? 0)}`,
          tone: "good",
          explanation: "Variante con più acquisti item-level nel periodo.",
        });
      }
    }
  }

  if (commerceMeta?.sales != null && commerceMeta.sales > 0) {
    const currency = commerceMeta.currency ? ` ${commerceMeta.currency}` : "";
    signals.push({
      key: "shopify-revenue",
      label: "Revenue Shopify",
      value: commerceMeta.sales.toLocaleString("it-IT", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }) + currency,
      tone: commerceMeta.sales >= 100 ? "good" : "warning",
      explanation: "Vendite aggregate nel periodo Shopify.",
    });
  }

  if (commerceMeta?.quantitySold != null) {
    signals.push({
      key: "shopify-quantity",
      label: "Vendite Shopify",
      value: _formatItalianNumber(commerceMeta.quantitySold),
      tone: commerceMeta.quantitySold > 0 ? "good" : "warning",
      explanation: "Unità vendute nel periodo.",
    });
  }

  if (commerceMeta?.ordersCount != null) {
    signals.push({
      key: "shopify-orders",
      label: "Ordini",
      value: _formatItalianNumber(commerceMeta.ordersCount),
      tone: commerceMeta.ordersCount > 0 ? "good" : "neutral",
      explanation: "Ordini Shopify che includono questo prodotto.",
    });
  }

  if (commerceMeta?.stock != null) {
    signals.push({
      key: "shopify-stock",
      label: "Stock",
      value: _formatItalianNumber(commerceMeta.stock),
      tone:
        commerceMeta.stock <= 0
          ? "danger"
          : commerceMeta.stock <= 10
            ? "warning"
            : "good",
      explanation: "Inventario totale prodotto su Shopify.",
    });
  }

  if (commerceMeta?.availableForSale != null) {
    signals.push({
      key: "shopify-availability",
      label: "Disponibilità",
      value: commerceMeta.availableForSale ? "Disponibile" : "Non disponibile",
      tone: commerceMeta.availableForSale ? "good" : "danger",
      explanation: "Stato vendibilità prodotto su Shopify.",
    });
  }

  if (gscMeta?.impressions != null) {
    const impressions = gscMeta.impressions;
    signals.push({
      key: "gsc-impressions",
      label: "Impression GSC",
      value: _formatItalianNumber(impressions),
      tone: impressions > 1000 ? "warning" : impressions >= 200 ? "neutral" : "good",
      explanation:
        impressions > 1000
          ? "Alta visibilità organica: ottimizzare CTR e snippet può generare click extra."
          : "Volume impression da Search Console.",
    });
  }

  if (gscMeta?.ctr != null) {
    const ctr = gscMeta.ctr;
    const impressions = gscMeta.impressions ?? 0;
    signals.push({
      key: "gsc-ctr",
      label: "CTR organico",
      value: _formatItalianPercent(ctr),
      tone: impressions > 200 && ctr < 0.01 ? "danger" : ctr < 0.02 ? "warning" : "good",
      explanation:
        impressions > 200 && ctr < 0.01
          ? "CTR basso rispetto alle impression: title e meta meritano attenzione."
          : "Click-through rate medio da Search Console.",
    });
  }

  if (gscMeta?.position != null) {
    const position = gscMeta.position;
    signals.push({
      key: "gsc-position",
      label: "Posizione media",
      value: position.toLocaleString("it-IT", { minimumFractionDigits: 1, maximumFractionDigits: 1 }),
      tone: position >= 4 && position <= 15 ? "warning" : position <= 3 ? "good" : "neutral",
      explanation:
        position >= 4 && position <= 15
          ? "Vicino alla prima pagina: contenuto mirato può spingere il ranking."
          : "Posizione media organica.",
    });
  }

  if (analyticsMeta?.sessions != null) {
    const sessions = analyticsMeta.sessions;
    signals.push({
      key: "ga4-sessions",
      label: "Sessioni GA4",
      value: _formatItalianNumber(sessions),
      tone: sessions > 300 ? "warning" : sessions >= 50 ? "neutral" : "good",
      explanation: "Traffico post-click misurato da GA4.",
    });
  }

  if (analyticsMeta?.conversions != null) {
    const conversions = analyticsMeta.conversions;
    const sessions = analyticsMeta.sessions ?? 0;
    signals.push({
      key: "ga4-conversions",
      label: "Conversioni GA4",
      value: _formatItalianNumber(conversions),
      tone: sessions > 50 && conversions === 0 ? "danger" : conversions > 0 ? "good" : "neutral",
      explanation:
        sessions > 50 && conversions === 0
          ? "Traffico senza conversioni: priorità CRO."
          : "Conversioni registrate nel periodo GA4.",
    });
  }

  if (analyticsMeta?.revenue != null) {
    signals.push({
      key: "ga4-revenue",
      label: "Revenue GA4",
      value: analyticsMeta.revenue.toLocaleString("it-IT", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
      tone: analyticsMeta.revenue > 0 ? "good" : "warning",
      explanation: "Ricavi attribuiti alla pagina in GA4.",
    });
  }

  if (performanceSnapshot.performanceScore != null) {
    const perfScore = performanceSnapshot.performanceScore;
    signals.push({
      key: "performance-score",
      label: "Performance score",
      value: String(perfScore),
      tone: perfScore < 50 ? "danger" : perfScore < 80 ? "warning" : "good",
      explanation: "Score Lighthouse/PageSpeed dell'ultima analisi.",
    });
  }

  if (croScore != null) {
    signals.push({
      key: "cro-score",
      label: "CRO score",
      value: String(croScore),
      tone: croScore < 70 ? "danger" : croScore < 80 ? "warning" : "good",
      explanation: "Valutazione persuasione e conversione da analisi AI.",
    });
  }

  if (openFindings.length > 0) {
    signals.push({
      key: "open-findings",
      label: "Problemi aperti",
      value: String(openFindings.length),
      tone: openFindings.some((f) => f.severity === "critical" || f.severity === "high")
        ? "danger"
        : "warning",
      explanation: "Findings tecnici o SEO ancora da risolvere.",
    });
  }

  if (priorityActionsCount > 0) {
    signals.push({
      key: "priority-actions",
      label: "Azioni prioritarie",
      value: String(priorityActionsCount),
      tone: priorityActionsCount >= 3 ? "warning" : "neutral",
      explanation: "Azioni già calcolate nel pannello sottostante.",
    });
  }

  return signals.slice(0, 6);
}

function _buildProductIntelligenceRecommendedActions(input: {
  context: ProductIntelligenceScoreContext;
  missingData: string[];
}): GrowthAuditProductIntelligenceAction[] {
  const { context, missingData } = input;
  const { gscMeta, analyticsMeta, commerceMeta, ga4EcommerceMeta, performanceSnapshot, croScore, aiLatestScore, openFindings } = context;
  const actions: GrowthAuditProductIntelligenceAction[] = [];

  const impressions = gscMeta?.impressions ?? 0;
  const ctr = gscMeta?.ctr ?? 0;
  const position = gscMeta?.position ?? 0;
  const sessions = analyticsMeta?.sessions ?? 0;
  const conversions = analyticsMeta?.conversions ?? 0;
  const perfScore = performanceSnapshot.performanceScore;
  const sales = commerceMeta?.sales ?? 0;
  const stock = commerceMeta?.stock;
  const availableForSale = commerceMeta?.availableForSale;
  const hasCriticalFindings = openFindings.some(
    (finding) => finding.severity === "critical" || finding.severity === "high",
  );

  const funnelViews = ga4EcommerceMeta?.itemViews ?? ga4EcommerceMeta?.itemViewEvents ?? 0;
  const funnelCart = ga4EcommerceMeta?.itemsAddedToCart ?? 0;
  const funnelPurchases = ga4EcommerceMeta?.itemsPurchased ?? 0;
  const funnelRevenue = ga4EcommerceMeta?.itemRevenue ?? 0;

  if (ga4EcommerceMeta && funnelViews > 50 && funnelCart === 0) {
    actions.push({
      title: "Migliora offerta, immagini e CTA",
      reason: "GA4 mostra visualizzazioni prodotto ma pochi add to cart.",
      expectedImpact: "Più add to cart e miglior View → Cart rate.",
      whereToFix: "Pagina prodotto Shopify / immagini / prezzo / CTA / trust",
      howToValidate: "Controlla View → Cart rate nei prossimi 14/30 giorni.",
    });
  }

  if (ga4EcommerceMeta && funnelCart > 0 && funnelPurchases === 0) {
    actions.push({
      title: "Analizza frizione tra carrello e acquisto",
      reason: "GA4 mostra add to cart ma pochi acquisti.",
      expectedImpact: "Più purchase e item revenue dal funnel esistente.",
      whereToFix: "Carrello, checkout, spedizione, costi finali, trust",
      howToValidate: "Controlla Cart → Purchase rate.",
    });
  }

  if (ga4EcommerceMeta && (funnelPurchases > 0 || funnelRevenue > 0)) {
    actions.push({
      title: "Scala una pagina che già monetizza",
      reason: "GA4 mostra acquisti o item revenue. Le ottimizzazioni possono amplificare un prodotto già validato.",
      expectedImpact: "Maggiore item revenue da un funnel già attivo.",
      whereToFix: "SEO snippet, CRO, immagini, performance, trust",
      howToValidate: "Confronta item revenue e purchase dopo le modifiche.",
    });
  }

  if (ga4EcommerceMeta && ga4EcommerceMeta.matchedBy === "none") {
    actions.push({
      title: "Verifica tracciamento ecommerce GA4",
      reason:
        impressions > 0 || sessions > 0 || sales > 0
          ? "Il prodotto ha segnali di traffico/vendita, ma il funnel item-level non è stato abbinato."
          : "Il prodotto non è stato abbinato in modo affidabile ai dati item-level.",
      expectedImpact: "Dati funnel affidabili per decisioni CRO.",
      whereToFix: "GA4 ecommerce tracking / Shopify channel / item_id / SKU",
      howToValidate:
        "Controlla item_id, SKU e configurazione ecommerce Shopify → GA4.",
    });
  }

  const matchedVariants = (ga4EcommerceMeta?.variantBreakdown ?? []).filter(
    (variant) => variant.matchedBy && variant.matchedBy !== "none",
  );
  if (matchedVariants.length > 0) {
    const totalVariantRevenue = matchedVariants.reduce(
      (sum, variant) => sum + (variant.itemRevenue ?? 0),
      0,
    );
    const bestRevenueVariant = matchedVariants.find(
      (variant) => variant.variantLegacyId === ga4EcommerceMeta?.bestVariantByRevenue,
    );
    if (
      bestRevenueVariant &&
      totalVariantRevenue > 0 &&
      (bestRevenueVariant.itemRevenue ?? 0) / totalVariantRevenue > 0.6
    ) {
      actions.push({
        title: "Ottimizza la variante più redditizia",
        reason: `${bestRevenueVariant.variantTitle || bestRevenueVariant.variantLegacyId} genera gran parte della item revenue.`,
        expectedImpact: "Maggiore revenue concentrando ottimizzazioni sulla variante vincente.",
        whereToFix: "Immagini, stock, copy e CTA della variante principale",
        howToValidate: "Confronta item revenue per variante nei prossimi 30 giorni.",
      });
    }

    const highDemandLowConversion = matchedVariants.find((variant) => {
      const views = variant.itemViews ?? variant.itemViewEvents ?? 0;
      return views > 50 && (variant.itemsPurchased ?? 0) === 0;
    });
    if (highDemandLowConversion) {
      actions.push({
        title: "Analizza variante con domanda non convertita",
        reason: `${highDemandLowConversion.variantTitle || highDemandLowConversion.variantLegacyId} ha view item alte ma pochi acquisti.`,
        expectedImpact: "Più purchase dalla variante con domanda già visibile.",
        whereToFix: "Prezzo, immagini, stock e copy della variante specifica",
        howToValidate: "Monitora View → Purchase rate per quella variante.",
      });
    }

    const outOfStockDemand = matchedVariants.find((variant) => {
      const views = variant.itemViews ?? variant.itemViewEvents ?? 0;
      const cart = variant.itemsAddedToCart ?? 0;
      return (variant.stock ?? 1) <= 0 && (views > 0 || cart > 0);
    });
    if (outOfStockDemand) {
      actions.push({
        title: "Risolvi stock della variante con domanda",
        reason: `${outOfStockDemand.variantTitle || outOfStockDemand.variantLegacyId} genera view/cart ma risulta senza stock.`,
        expectedImpact: "Recupero vendite perse su una variante già richiesta.",
        whereToFix: "Shopify inventory della variante",
        howToValidate: "Verifica purchase e item revenue dopo il ripristino stock.",
      });
    }
  }

  if (sales > 0 && hasCriticalFindings) {
    actions.push({
      title: "Dai priorità a questa pagina: prodotto già monetizza",
      reason: "Shopify mostra vendite/revenue nel periodo. Migliorare la pagina può amplificare un prodotto già validato.",
      expectedImpact: "Maggiore revenue da un prodotto già validato dal mercato.",
      whereToFix: "Shopify prodotto / contenuto / immagini / trust / performance",
      howToValidate: "Confronta revenue, conversioni e CTR nei prossimi 14/30 giorni.",
    });
  }

  if (
    commerceMeta &&
    (impressions > 200 || sessions > 50) &&
    sales === 0 &&
    (commerceMeta.quantitySold ?? 0) === 0
  ) {
    actions.push({
      title: "Trasforma traffico in vendite",
      reason: "La pagina riceve segnali di domanda ma Shopify non mostra vendite nel periodo.",
      expectedImpact: "Più purchase e revenue da traffico esistente.",
      whereToFix: "Offerta, trust, CTA, immagini, prezzo, spedizione, FAQ",
      howToValidate: "Monitora add to cart, purchase e vendite Shopify.",
    });
  }

  if (
    commerceMeta &&
    (sales > 0 || impressions > 200 || sessions > 50) &&
    (stock != null && stock <= 0 || availableForSale === false)
  ) {
    actions.push({
      title: "Risolvi disponibilità prima di spingere traffico",
      reason: "Il prodotto ha segnali di domanda o vendite, ma lo stock può limitare conversioni.",
      expectedImpact: "Eviti traffico sprecato e recuperi vendite perse.",
      whereToFix: "Shopify inventory / disponibilità prodotto",
      howToValidate: "Verifica stock e vendite dopo il ripristino.",
    });
  }

  if (gscMeta && impressions > 200 && ctr < 0.02) {
    actions.push({
      title: "Riscrivi title e meta description con query reali",
      reason: "Search Console mostra impression ma pochi click.",
      expectedImpact: "Miglior CTR organico e più click sulle query principali.",
      whereToFix: "Modifica Shopify → campi SEO",
      howToValidate: "Dopo 14/30 giorni controlla CTR e click Search Console.",
    });
  }

  if (gscMeta && position >= 4 && position <= 15 && impressions >= 200) {
    actions.push({
      title: "Rafforza contenuto e FAQ sulle query principali",
      reason: "La pagina è vicina a posizioni più redditizie.",
      expectedImpact: "Più impression in top posizioni e traffico organico qualificato.",
      whereToFix: "Modifica Shopify → descrizione prodotto / FAQ",
      howToValidate: "Monitora posizione media e impression.",
    });
  }

  if (analyticsMeta && sessions > 50 && conversions === 0) {
    actions.push({
      title: "Rinforza trust, CTA e proposta d'acquisto",
      reason: "La pagina riceve traffico ma non converte abbastanza.",
      expectedImpact: "Più add to cart e conversioni da traffico esistente.",
      whereToFix: "Modifica Shopify → descrizione prodotto / sezioni trust",
      howToValidate: "Controlla add to cart, conversioni e revenue.",
    });
  }

  if (
    perfScore != null &&
    (perfScore < 80 ||
      _isPoorLcp(performanceSnapshot.lcp) ||
      _isPoorCls(performanceSnapshot.cls) ||
      _isPoorInp(performanceSnapshot.inp))
  ) {
    actions.push({
      title: "Ottimizza immagini e risorse above the fold",
      reason: "La velocità può ridurre conversione e qualità esperienza mobile.",
      expectedImpact: "Migliore LCP/CLS/INP e UX mobile più fluida.",
      whereToFix: "Tema Shopify / immagini prodotto / sviluppo",
      howToValidate: "Rilancia Performance e controlla LCP/CLS/INP.",
    });
  }

  if (
    (croScore != null && croScore < 70) ||
    (aiLatestScore != null && aiLatestScore < 70)
  ) {
    actions.push({
      title: "Completa contenuto persuasivo e risposte alle obiezioni",
      reason:
        "L'analisi AI/CRO rileva debolezze su fiducia, chiarezza o decisione d'acquisto.",
      expectedImpact: "Maggiore fiducia e chiarezza nella decisione d'acquisto.",
      whereToFix: "Modifica Shopify → descrizione, blocchi trust, FAQ",
      howToValidate: "Rilancia AI/GEO/CRO e monitora GA4.",
    });
  }

  if (missingData.length > 0) {
    actions.push({
      title: "Completa le analisi mancanti",
      reason: "Servono più dati per decidere priorità e impatto.",
      expectedImpact: "Priorità operativa più affidabile e meno rischio di interventi sbagliati.",
      whereToFix: "Sezioni Performance, Search Console, GA4, AI/GEO/CRO",
      howToValidate: "Verifica che la Product Intelligence mostri meno dati mancanti.",
    });
  }

  return actions.slice(0, 5);
}

function _emptyProductIntelligenceSummary(): GrowthAuditProductIntelligenceSummary {
  return {
    available: false,
    level: "monitor",
    score: 0,
    title: "",
    verdict: "",
    mainReason: "",
    evidence: [],
    missingData: [],
    recommendedActions: [],
  };
}

export function buildGrowthAuditProductIntelligenceSummary(input: {
  page: GrowthAuditPage;
  findings: GrowthAuditFinding[];
  tasks: GrowthAuditTask[];
  priorityActions: GrowthAuditPriorityAction[];
  aiResults?: GrowthAuditPageResult[];
  performanceResults?: GrowthAuditPageResult[];
  runSummary?: GrowthAuditRunSummary | null;
}): GrowthAuditProductIntelligenceSummary {
  const { page, findings, tasks, priorityActions, aiResults, performanceResults, runSummary } = input;

  if (!isGrowthAuditProductPage(page)) {
    return _emptyProductIntelligenceSummary();
  }

  const missingData = _buildProductIntelligenceMissingData(page, aiResults, performanceResults);
  const context = _computeProductPriorityScore({
    page,
    findings,
    tasks,
    performanceResults,
    runSummary: runSummary?.shopifyCommerce ?? null,
  });
  const level = _scoreToProductIntelligenceLevel(context.score);
  const { title, verdict, mainReason } = _buildProductIntelligenceVerdict({
    context,
    missingData,
  });
  const evidence = _buildProductIntelligenceEvidence({
    context,
    priorityActionsCount: priorityActions.length,
  });
  const recommendedActions = _buildProductIntelligenceRecommendedActions({
    context,
    missingData,
  });

  return {
    available: true,
    level,
    score: context.score,
    title,
    verdict,
    mainReason,
    evidence,
    missingData,
    recommendedActions,
  };
}
