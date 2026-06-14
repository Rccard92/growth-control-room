export type SeoIssueSeverity = "critical" | "warning" | "opportunity" | "info";
export type SeoIssueStatus = "open" | "ignored" | "resolved";
export type SeoEntityType = "product" | "collection" | "page" | "article" | "blog";

export type ContentOpportunityType =
  | "blog_topic"
  | "product_improvement"
  | "collection_improvement"
  | "internal_linking"
  | "faq"
  | "comparison";

export type ContentOpportunityPriority = "high" | "medium" | "low";
export type ContentOpportunityStatus = "new" | "planned" | "drafted" | "published" | "ignored";
export type ContentBriefStatus = "draft" | "approved" | "exported" | "published";
export type SearchIntent = "informational" | "commercial" | "transactional";

export interface SeoAuditIssue {
  id: string;
  entityType: SeoEntityType;
  entityId: string;
  issueType: string;
  severity: SeoIssueSeverity;
  title: string;
  description: string;
  recommendation: string;
  status: SeoIssueStatus;
  createdAt?: string | null;
}

export interface ContentEntityRef {
  id: string;
  handle?: string | null;
  title?: string | null;
  entityType?: string;
}

export interface ContentOpportunity {
  id: string;
  opportunityType: ContentOpportunityType;
  priority: ContentOpportunityPriority;
  title: string;
  description: string;
  targetEntityType?: string | null;
  targetEntityId?: string | null;
  suggestedKeyword?: string | null;
  searchIntent?: SearchIntent | null;
  suggestedProducts?: ContentEntityRef[] | null;
  suggestedCollections?: ContentEntityRef[] | null;
  reason: string;
  status: ContentOpportunityStatus;
  createdAt?: string | null;
}

export interface ContentBrief {
  id: string;
  title: string;
  primaryKeyword?: string | null;
  secondaryKeywords?: string[] | null;
  searchIntent?: SearchIntent | null;
  outline?: Record<string, unknown> | null;
  internalLinks?: ContentEntityRef[] | null;
  productsToFeature?: ContentEntityRef[] | null;
  faq?: Record<string, unknown>[] | null;
  cta?: string | null;
  status: ContentBriefStatus;
}

export interface ContentSeoDashboardSummary {
  totalIssues: number;
  criticalIssues: number;
  warnings: number;
  opportunities: number;
  contentOpportunities: number;
  productsWithoutMeta: number;
  collectionsWeak: number;
  articlesWeak: number;
  hasSyncedContent?: boolean;
  contentEntitiesCount?: number;
}

export interface ContentSeoDashboard {
  summary: ContentSeoDashboardSummary;
  issues: SeoAuditIssue[];
  opportunities: ContentOpportunity[];
  topProductOpportunities: ContentOpportunity[];
  topCollectionOpportunities: ContentOpportunity[];
  internalLinkingOpportunities: ContentOpportunity[];
}

export interface ContentSeoSyncResponse {
  collectionsSynced: number;
  pagesSynced: number;
  blogsSynced: number;
  articlesSynced: number;
  durationSeconds: number;
}

export interface ContentSeoAnalyzeResponse {
  issuesCreated: number;
  opportunitiesCreated: number;
  criticalIssues: number;
  highPriorityOpportunities: number;
}

export type SeoOptimizerSeverity = "critical" | "warning" | "opportunity" | "good";
export type SeoProposalStatus = "draft" | "approved" | "applied" | "rejected";
export type SeoOptimizerTab = "products" | "collections" | "editorial";

export interface SeoOptimizerSyncResponse {
  productsSynced: number;
  collectionsSynced: number;
  pagesSynced?: number;
  blogsSynced?: number;
  articlesSynced?: number;
  durationSeconds: number;
  warnings?: string[];
  message?: string | null;
}

export interface SeoAnalyzeCountResponse {
  productsAnalyzed?: number;
  collectionsAnalyzed?: number;
  critical: number;
  warnings: number;
  opportunities: number;
  message?: string | null;
}

export interface SeoContentDebugResponse {
  productsCount: number;
  collectionsCount: number;
  collectionAnalysesCount: number;
  lastContentSync?: string | null;
  lastErrors: string[];
}

export interface SeoProductListItem {
  id: string;
  shopifyGid: string;
  title: string;
  handle?: string | null;
  score?: number | null;
  severity?: SeoOptimizerSeverity | null;
  mainIssues: string[];
  quantitySold: number;
  revenue: number;
  stock?: number | null;
  hasProposal: boolean;
  analysisId?: string | null;
}

export interface SeoCollectionListItem {
  id: string;
  shopifyGid: string;
  title: string;
  handle?: string | null;
  score?: number | null;
  severity?: SeoOptimizerSeverity | null;
  mainIssues: string[];
  productsCount?: number | null;
  hasProposal: boolean;
  analysisId?: string | null;
}

export interface SeoProductListResponse {
  items: SeoProductListItem[];
  openaiConfigured: boolean;
  writeProductsAvailable: boolean;
}

export interface SeoCollectionListResponse {
  items: SeoCollectionListItem[];
  openaiConfigured: boolean;
  writeProductsAvailable: boolean;
}

export interface SeoScoreBreakdownItem {
  score: number;
  max: number;
  issues: Record<string, unknown>[];
}

export type SeoScoreBreakdown = Record<string, SeoScoreBreakdownItem>;

export interface SeoEntityAnalysis {
  id: string;
  entityType: "product" | "collection";
  entityId: string;
  entityTitle: string;
  scoreTotal: number;
  scoreTitle: number;
  scoreSeoTitle: number;
  scoreMetaDescription: number;
  scoreDescription: number;
  scoreImageAlt: number;
  scoreHandle: number;
  scoreTags: number;
  severity: SeoOptimizerSeverity;
  issues?: Record<string, unknown>[] | null;
  recommendations?: Record<string, unknown>[] | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  lastAnalyzedAt?: string | null;
}

export type SeoProposalSource = "ai" | "rules" | "manual";

export interface SeoOptimizationProposal {
  id: string;
  entityType: "product" | "collection";
  entityId: string;
  entityGid: string;
  status: SeoProposalStatus;
  source: SeoProposalSource;
  currentValues?: Record<string, unknown> | null;
  proposedValues?: Record<string, unknown> | null;
  reasoning?: unknown[] | null;
  riskLevel: "low" | "medium" | "high";
  approvedAt?: string | null;
  appliedAt?: string | null;
  createdAt?: string | null;
  changedFields?: string[];
}

export interface SeoProposalGenerateFieldResponse {
  field: string;
  value: unknown;
  reasoning?: string | null;
  riskLevel: "low" | "medium" | "high";
  metafieldId?: string | null;
  definitionId?: string | null;
}

export interface SeoMetafieldDefinitionsSyncResponse {
  definitionsSynced: number;
  ownerType: string;
  warnings: string[];
}

export interface SeoProposalPreviewField {
  field: string;
  current?: unknown;
  proposed?: unknown;
  changed: boolean;
  reasoning?: string | null;
  risk?: string | null;
}

export interface SeoProposalPreviewResponse {
  proposalId: string;
  entityType: "product" | "collection";
  entityId: string;
  status: SeoProposalStatus;
  source: SeoProposalSource;
  riskLevel: "low" | "medium" | "high";
  reasoning?: unknown[] | null;
  fields: SeoProposalPreviewField[];
  changedFields: string[];
  currentValues?: Record<string, unknown> | null;
  proposedValues?: Record<string, unknown> | null;
}

export interface SeoChangeLogEntry {
  id: string;
  status: string;
  appliedValues?: Record<string, unknown> | null;
  errorMessage?: string | null;
  createdAt?: string | null;
  proposalId: string;
}

export interface SeoSkillMeta {
  name: string;
  version: string;
  attribution: string;
  scoreRuleCategories: string[];
  externalSkills?: string[];
}

export interface SeoProductMetafieldItem {
  id: string;
  definitionId: string;
  metafieldId?: string | null;
  namespace: string;
  key: string;
  type: string;
  value: string;
  rawValue?: string;
  displayValue?: string;
  definitionName?: string | null;
  definitionDescription?: string | null;
  editable: boolean;
  aiGeneratable: boolean;
  existsOnProduct?: boolean;
  isEmpty?: boolean;
  updatedAt?: string | null;
}

export interface SeoProductDetailResponse {
  product: Record<string, unknown>;
  analysis?: Record<string, unknown> | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  skillMeta?: SeoSkillMeta | null;
  currentValues: Record<string, unknown>;
  images: Record<string, unknown>[];
  metafields?: SeoProductMetafieldItem[];
  metafieldDefinitionsCount?: number;
  hasMetafieldDefinitions?: boolean;
  quantitySold: number;
  revenue: number;
  stock?: number | null;
  latestProposal?: SeoOptimizationProposal | null;
  proposalHistory: SeoOptimizationProposal[];
  changeLogs: SeoChangeLogEntry[];
}

export interface SeoCollectionDetailResponse {
  collection: Record<string, unknown>;
  analysis?: Record<string, unknown> | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  skillMeta?: SeoSkillMeta | null;
  currentValues: Record<string, unknown>;
  image?: Record<string, unknown> | null;
  latestProposal?: SeoOptimizationProposal | null;
  proposalHistory: SeoOptimizationProposal[];
  changeLogs: SeoChangeLogEntry[];
}

export interface SeoProposalListResponse {
  items: SeoOptimizationProposal[];
}

export interface SeoApplyFieldsRequest {
  entityType: "product" | "collection";
  entityId: string;
  fields: Record<string, unknown>;
  changedFields: string[];
}

export interface SeoApplyFieldsResponse extends SeoApplyResponse {
  appliedFields?: string[];
}

export interface SeoApplyResponse {
  applied: boolean;
  requiresScope?: string | null;
  requiresReconnect?: boolean;
  localUpdateFailed?: boolean;
  entityType?: string | null;
  entityId?: string | null;
  updatedEntity?: Record<string, unknown> | null;
  updatedAnalysis?: Record<string, unknown> | null;
  detail?: Record<string, unknown> | null;
  proposal?: SeoOptimizationProposal | null;
  message?: string | null;
  proposalId?: string | null;
  appliedFields?: string[];
}

export interface SeoEntitySyncResponse {
  entityType: "product" | "collection";
  entityId: string;
  detail: SeoProductDetailResponse | SeoCollectionDetailResponse;
  message: string;
}

// --- Content SEO Editorial (Blog & Ricette) ---

export type ContentSeoMainTab = "products" | "editorial";

export type ContentSeoEditorialStatus =
  | "idea"
  | "brief_pending"
  | "brief_approved"
  | "draft_pending"
  | "draft_review"
  | "ready_to_publish"
  | "scheduled"
  | "published"
  | "publish_error";

export type ContentSeoEditorialContentType =
  | "educational_article"
  | "product_guide"
  | "recipe"
  | "faq_objection_article"
  | "product_comparison"
  | "seasonal_article"
  | "brand_storytelling";

export type ContentSeoEditorialObjective =
  | "seo_traffic"
  | "education"
  | "push_products"
  | "answer_objections"
  | "support_ads"
  | "support_email"
  | "seasonal_content";

export type ContentSeoEditorialCommercialIntensity = "soft" | "balanced" | "sales_oriented";

export type ContentSeoEditorialFrequency =
  | "daily"
  | "every_2_days"
  | "every_3_days"
  | "every_4_days"
  | "weekly"
  | "twice_weekly"
  | "custom";

export type EditorialWeekday =
  | "monday"
  | "tuesday"
  | "wednesday"
  | "thursday"
  | "friday"
  | "saturday"
  | "sunday";

export const CONTENT_SEO_EDITORIAL_STATUS_LABELS: Record<ContentSeoEditorialStatus, string> = {
  idea: "Idea",
  brief_pending: "Brief in attesa",
  brief_approved: "Brief approvato",
  draft_pending: "Bozza in attesa",
  draft_review: "Bozza in revisione",
  ready_to_publish: "Pronto per pubblicazione",
  scheduled: "Programmato",
  published: "Pubblicato",
  publish_error: "Errore pubblicazione",
};

export const CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS: Record<
  ContentSeoEditorialContentType,
  string
> = {
  educational_article: "Articolo educativo",
  product_guide: "Guida prodotto",
  recipe: "Ricetta",
  faq_objection_article: "FAQ/obiezione in articolo",
  product_comparison: "Confronto tra prodotti",
  seasonal_article: "Articolo stagionale",
  brand_storytelling: "Storytelling brand/prodotto",
};

export const CONTENT_SEO_EDITORIAL_OBJECTIVE_LABELS: Record<
  ContentSeoEditorialObjective,
  string
> = {
  seo_traffic: "Aumentare traffico SEO",
  education: "Educare il pubblico",
  push_products: "Spingere prodotti specifici",
  answer_objections: "Rispondere a obiezioni frequenti",
  support_ads: "Supportare campagne ads",
  support_email: "Supportare email marketing",
  seasonal_content: "Preparare contenuti stagionali",
};

export interface ContentSeoEditorialItem {
  id: string;
  projectId: string;
  title: string;
  contentType: ContentSeoEditorialContentType;
  plannedDate: string;
  status: ContentSeoEditorialStatus;
  objective?: ContentSeoEditorialObjective | null;
  primaryKeyword?: string | null;
  secondaryKeywords?: string[] | null;
  targetAudience?: string | null;
  searchIntent?: string | null;
  commercialIntensity?: ContentSeoEditorialCommercialIntensity | null;
  linkedShopifyProductId?: string | null;
  linkedShopifyProductGid?: string | null;
  linkedShopifyProductTitle?: string | null;
  linkedShopifyProductHandle?: string | null;
  linkedCollectionId?: string | null;
  linkedCollectionTitle?: string | null;
  notes?: string | null;
  briefPayload?: Record<string, unknown> | null;
  articlePayload?: Record<string, unknown> | null;
  shopifyBlogId?: string | null;
  shopifyArticleId?: string | null;
  shopifyStatus?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ContentSeoEditorialItemCreate {
  title: string;
  contentType: ContentSeoEditorialContentType;
  plannedDate: string;
  status?: ContentSeoEditorialStatus;
  objective?: ContentSeoEditorialObjective | null;
  primaryKeyword?: string | null;
  secondaryKeywords?: string[] | null;
  notes?: string | null;
  linkedShopifyProductId?: string | null;
  linkedShopifyProductGid?: string | null;
  linkedShopifyProductTitle?: string | null;
  linkedShopifyProductHandle?: string | null;
}

export interface ContentSeoEditorialItemUpdate {
  title?: string;
  contentType?: ContentSeoEditorialContentType;
  plannedDate?: string;
  status?: ContentSeoEditorialStatus;
  objective?: ContentSeoEditorialObjective | null;
  primaryKeyword?: string | null;
  secondaryKeywords?: string[] | null;
  notes?: string | null;
  linkedShopifyProductId?: string | null;
  linkedShopifyProductGid?: string | null;
  linkedShopifyProductTitle?: string | null;
  linkedShopifyProductHandle?: string | null;
}

export interface ContentSeoEditorialItemListResponse {
  items: ContentSeoEditorialItem[];
  month?: string | null;
}

export interface EditorialPlanGenerateRequest {
  startDate: string;
  endDate: string;
  frequency: ContentSeoEditorialFrequency;
  preferredWeekdays?: EditorialWeekday[] | null;
  contentTypes: ContentSeoEditorialContentType[];
  objectives?: ContentSeoEditorialObjective[];
  objective?: ContentSeoEditorialObjective;
  commercialIntensity: ContentSeoEditorialCommercialIntensity;
  linkedProductIds?: string[];
  avoidProductIds?: string[];
  primaryKeywords?: string[];
  notes?: string;
}

export interface EditorialPlanGenerateResponse {
  items: ContentSeoEditorialItem[];
  dryRun: boolean;
  message: string;
}

export interface EditorialItemRescheduleRequest {
  plannedDate: string;
  cascade?: boolean;
}

export interface EditorialItemRescheduleResponse {
  items: ContentSeoEditorialItem[];
  deltaDays: number;
  warning?: string | null;
}

export interface EditorialBriefPayload {
  proposedTitle: string;
  searchIntent: string;
  targetAudience: string;
  primaryKeyword: string;
  secondaryKeywords: string[];
  contentAngle: string;
  h2H3Structure: string[];
  productsToLink: string[];
  faqToInclude: string[];
  claimsToAvoid: string[];
  safeClaimsToUse: string[];
  recommendedCta: string;
  metaTitle: string;
  metaDescription: string;
  internalLinksSuggestions: string[];
  notes: string;
  brandContextUsed: string[];
  warnings: string[];
}

export type EditorialBriefUpdateStatus = "brief_pending" | "brief_approved";

export interface EditorialBriefUpdateRequest {
  briefPayload: EditorialBriefPayload;
  status?: EditorialBriefUpdateStatus;
}
