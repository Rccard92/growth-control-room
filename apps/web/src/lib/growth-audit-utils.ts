import type {
  GrowthAuditInventoryCounts,
  GrowthAuditInventoryFilter,
  GrowthAuditPage,
  GrowthAuditPageType,
  GrowthAuditRunStatus,
  GrowthAuditRunSummary,
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
  if (summary?.warning) return summary.warning;
  if (pagesDiscovered > 1) {
    return "Inventario creato. Nel prossimo step potrai avviare l'analisi per tipologia di pagina.";
  }
  if (pagesDiscovered === 1) {
    return "È stata trovata solo la pagina seed. Nel prossimo step potremmo dover configurare meglio sitemap o discovery Shopify.";
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
