export interface BrandProfile {
  id: string;
  projectId: string;
  brandName?: string | null;
  websiteUrl?: string | null;
  industry?: string | null;
  country?: string | null;
  shortDescription?: string | null;
  story?: string | null;
  mission?: string | null;
  values?: string[] | null;
  differentiators?: string[] | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandVoice {
  id: string;
  projectId: string;
  tone?: string | null;
  styleNotes?: string | null;
  formalityLevel?: string | null;
  emojiPolicy?: string | null;
  wordsToUse?: string[] | null;
  wordsToAvoid?: string[] | null;
  examplesGood?: string[] | null;
  examplesBad?: string[] | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandProductKnowledge {
  id: string;
  projectId: string;
  name: string;
  entityType: "product" | "category";
  shopifyGid?: string | null;
  description?: string | null;
  ingredients?: string | null;
  origin?: string | null;
  productionProcess?: string | null;
  usageSuggestions?: string | null;
  conservation?: string | null;
  tasteNotes?: string | null;
  objections?: string[] | null;
  faq?: Array<{ question?: string; answer?: string }> | null;
  claimsAllowed?: string[] | null;
  claimsForbidden?: string[] | null;
  relatedProducts?: string[] | null;
  priority: "high" | "medium" | "low";
  createdAt: string;
  updatedAt: string;
}

export interface BrandAudienceInsight {
  id: string;
  projectId: string;
  segmentName: string;
  description?: string | null;
  motivations?: string[] | null;
  painPoints?: string[] | null;
  objections?: string[] | null;
  questions?: string[] | null;
  buyingTriggers?: string[] | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandClaimRule {
  id: string;
  projectId: string;
  ruleType: "allowed" | "forbidden" | "caution" | "disclaimer";
  title: string;
  description?: string | null;
  examples?: string[] | null;
  severity: "critical" | "warning" | "info";
  createdAt: string;
  updatedAt: string;
}

export interface BrandSeoStrategy {
  id: string;
  projectId: string;
  primaryKeywords?: string[] | null;
  secondaryKeywords?: string[] | null;
  keywordClusters?: Array<Record<string, unknown>> | null;
  priorityPages?: string[] | null;
  internalLinkingNotes?: string | null;
  metaTitlePattern?: string | null;
  metaDescriptionPattern?: string | null;
  urlHandlePattern?: string | null;
  competitors?: string[] | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandContentPillar {
  id: string;
  projectId: string;
  name: string;
  description?: string | null;
  objective?: string | null;
  products?: string[] | null;
  channels?: string[] | null;
  exampleTopics?: string[] | null;
  ctaNotes?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandAiGuardrail {
  id: string;
  projectId: string;
  title: string;
  description?: string | null;
  ruleType: "must" | "must_not" | "caution";
  appliesTo?: string[] | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandAsset {
  id: string;
  projectId: string;
  assetType: "logo" | "color" | "font" | "image" | "video" | "document" | "other";
  name: string;
  value?: string | null;
  fileUrl?: string | null;
  notes?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandKnowledgeScore {
  overallScore: number;
  status: "incomplete" | "developing" | "ready";
  sectionScores: Record<string, number>;
  missingRequired: string[];
  recommendations: string[];
}

export interface BrandSectionStatus {
  key: string;
  label: string;
  complete: boolean;
  score: number;
}

export interface BrandIntelligenceOverview {
  score: BrandKnowledgeScore;
  sections: BrandSectionStatus[];
  hasProfile: boolean;
  hasVoice: boolean;
  productsCount: number;
  audienceCount: number;
  claimsCount: number;
  guardrailsCount: number;
  pillarsCount: number;
  assetsCount: number;
  sourceDocumentsCount?: number;
  pendingFactsCount?: number;
  pendingSectionDraftsCount?: number;
  latestBatchId?: string | null;
}

export type SectionDraftKey =
  | "brand_profile"
  | "voice_tone"
  | "products_categories"
  | "audience"
  | "claims_compliance"
  | "seo_strategy"
  | "content_pillars"
  | "ai_guardrails"
  | "assets";

export type SectionDraftStatus = "draft" | "needs_review" | "approved" | "rejected" | "applied";

export interface SectionDraftWarnings {
  messages?: string[];
  missingInformation?: string[];
}

export interface BrandSectionDraftListItem {
  id: string;
  batchId?: string | null;
  sectionKey: SectionDraftKey;
  title: string;
  summary?: string | null;
  confidence?: number | null;
  status: SectionDraftStatus;
  sourceFactIds?: string[];
  sourceExternalIds?: string[];
  warnings?: SectionDraftWarnings | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandSectionDraft extends BrandSectionDraftListItem {
  projectId: string;
  draftPayload: unknown;
  sourceDocumentIds?: string[];
  sourceExternalIds?: string[];
  aiReasoning?: string | null;
  previousOfficialSnapshot?: unknown;
  approvedAt?: string | null;
  appliedAt?: string | null;
}

export interface BrandSectionDraftSynthesizeResponse {
  batchId: string;
  draftsCreated: number;
  sections: Array<{
    sectionKey: SectionDraftKey;
    status: SectionDraftStatus;
    confidence?: number | null;
  }>;
}

export interface BrandSectionDraftApplyResultItem {
  draftId: string;
  sectionKey: string;
  status: string;
  message: string;
}

export interface BrandSectionDraftApplyResponse {
  applied?: BrandSectionDraftApplyResultItem[];
  skipped?: BrandSectionDraftApplyResultItem[];
  conflicts?: BrandSectionDraftApplyResultItem[];
}

export type DocumentExtractionStatus =
  | "uploaded"
  | "extracting"
  | "extracted"
  | "failed"
  | "reviewed";

export type FactStatus = "suggested" | "approved" | "rejected" | "needs_review";

export type TargetSection =
  | "brand_profile"
  | "voice_tone"
  | "product_knowledge"
  | "category_knowledge"
  | "audience"
  | "claims_compliance"
  | "seo_strategy"
  | "content_pillars"
  | "ai_guardrails"
  | "assets"
  | "unknown";

export interface BrandSourceDocument {
  id: string;
  projectId: string;
  batchId?: string | null;
  filename: string;
  contentType: string;
  fileSize?: number;
  storageMode?: string;
  documentType?: string | null;
  documentSummary?: string | null;
  extractionStatus: DocumentExtractionStatus | string;
  extractionError?: string | null;
  processingOrder?: number | null;
  progressPercent?: number;
  currentStep?: string | null;
  uploadedAt?: string;
  processedAt?: string | null;
  createdAt?: string;
  updatedAt?: string;
}

export interface BrandSourceDocumentUploadItem {
  id: string;
  filename: string;
  status: string;
}

export type ExternalSourceType =
  | "website"
  | "instagram"
  | "facebook"
  | "tiktok"
  | "youtube"
  | "linkedin"
  | "trustpilot"
  | "google_business"
  | "other";

export type ExternalSourceStatus =
  | "pending"
  | "fetching"
  | "fetched"
  | "failed"
  | "skipped";

export interface BrandExternalSourceInput {
  sourceType: ExternalSourceType;
  url: string;
  label?: string | null;
}

export interface BrandExternalSource {
  id: string;
  projectId: string;
  batchId?: string | null;
  sourceType: ExternalSourceType;
  label?: string | null;
  url: string;
  status: ExternalSourceStatus;
  fetchedTitle?: string | null;
  fetchedText?: string | null;
  fetchedSummary?: string | null;
  fetchError?: string | null;
  lastFetchedAt?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandExternalSourcesFormValues {
  brandName: string;
  websiteUrl: string;
  instagramUrl: string;
  facebookUrl: string;
  tiktokUrl: string;
  youtubeUrl: string;
  linkedinUrl: string;
  trustpilotUrl: string;
  googleBusinessUrl: string;
  otherSources: Array<{ label: string; url: string }>;
}

export interface BrandSourceDocumentsUploadResponse {
  batchId: string;
  status: string;
  documents: BrandSourceDocumentUploadItem[];
  externalSources?: BrandExternalSource[];
}

export type ImportBatchStatus =
  | "pending"
  | "uploading"
  | "extracting"
  | "ai_processing"
  | "review_ready"
  | "partially_failed"
  | "completed"
  | "failed";

export type UpdateMode = "create" | "enrich" | "update" | "duplicate_candidate" | "unknown";
export type ConflictStatus = "none" | "possible_conflict" | "confirmed_conflict";

export interface BrandImportBatchDocumentStatus {
  id: string;
  filename: string;
  extractionStatus: string;
  progressPercent: number;
  currentStep?: string | null;
  extractedFactsCount: number;
  extractionError?: string | null;
}

export interface BrandImportBatch {
  id: string;
  projectId: string;
  name?: string | null;
  sourceType: string;
  notes?: string | null;
  status: ImportBatchStatus;
  progressPercent: number;
  currentStep?: string | null;
  totalFiles: number;
  processedFiles: number;
  totalFacts: number;
  approvedFacts: number;
  rejectedFacts: number;
  needsReviewFacts: number;
  errorMessage?: string | null;
  warnings: string[];
  declaredBrandName?: string | null;
  declaredWebsiteUrl?: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandImportBatchStatusResponse extends BrandImportBatch {
  documents: BrandImportBatchDocumentStatus[];
  externalSources?: BrandExternalSource[];
}

export interface BrandImportBatchListItem {
  id: string;
  name?: string | null;
  sourceType: string;
  status: ImportBatchStatus;
  progressPercent: number;
  totalFiles: number;
  totalFacts: number;
  needsReviewFacts: number;
  createdAt: string;
  completedAt?: string | null;
}

export interface BrandImportBatchStartResponse {
  batchId: string;
  status: string;
}

export interface BrandExtractedFact {
  id: string;
  projectId: string;
  sourceDocumentId?: string | null;
  sourceExternalId?: string | null;
  batchId?: string | null;
  targetSection: TargetSection;
  targetEntityType?: string | null;
  fieldName?: string | null;
  extractedValue?: unknown;
  sourceExcerpt?: string | null;
  confidence: number;
  status: FactStatus;
  aiReasoning?: string | null;
  isUpdateSuggestion?: boolean;
  existingTargetId?: string | null;
  updateMode?: UpdateMode;
  previousValue?: unknown;
  conflictStatus?: ConflictStatus;
  sourceCreatedAt?: string | null;
  importRound?: number | null;
  reviewedAt?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandExtractBatchResult {
  documentId: string;
  status: string;
  factsCount: number;
  error?: string | null;
}

export interface BrandExtractBatchResponse {
  results: BrandExtractBatchResult[];
}

export interface BrandApplyFactsResultItem {
  factId: string;
  targetSection: string;
  fieldName?: string | null;
  message: string;
}

export interface BrandApplyFactsResponse {
  saved: BrandApplyFactsResultItem[];
  skipped: BrandApplyFactsResultItem[];
  counts: {
    saved: number;
    skipped: number;
    needsReview: number;
    rejected: number;
  };
}

export interface BrandContextBundle {
  profile?: BrandProfile | null;
  voice?: BrandVoice | null;
  products: BrandProductKnowledge[];
  categories: BrandProductKnowledge[];
  audience: BrandAudienceInsight[];
  claims: BrandClaimRule[];
  seoStrategy?: BrandSeoStrategy | null;
  contentPillars: BrandContentPillar[];
  guardrails: BrandAiGuardrail[];
  assets: BrandAsset[];
  knowledgeScore: BrandKnowledgeScore;
}

export type BrandIntelligenceTab =
  | "overview"
  | "wizard"
  | "import"
  | "profile"
  | "voice"
  | "products"
  | "audience"
  | "claims"
  | "seo"
  | "pillars"
  | "guardrails"
  | "assets"
  | "sources";
