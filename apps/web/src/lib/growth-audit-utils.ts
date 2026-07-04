import type {
  GrowthAuditFinding,
  GrowthAuditInventoryCounts,
  GrowthAuditInventoryFilter,
  GrowthAuditPage,
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

export function getDefaultRootUrl(shopDomain?: string | null): string {
  if (!shopDomain) return "";
  const trimmed = shopDomain.trim();
  if (!trimmed) return "";
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    return trimmed;
  }
  return `https://${trimmed}`;
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
      label: "Site Score",
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
