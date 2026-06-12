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
