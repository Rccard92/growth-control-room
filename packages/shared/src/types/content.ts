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
export type SeoOptimizerTab = "products" | "collections" | "proposals" | "editorial";

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
