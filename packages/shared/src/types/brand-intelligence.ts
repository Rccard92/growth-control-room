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
  filename: string;
  contentType: string;
  fileSize: number;
  storageMode: string;
  documentType?: string | null;
  documentSummary?: string | null;
  extractionStatus: DocumentExtractionStatus;
  extractionError?: string | null;
  uploadedAt: string;
  processedAt?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface BrandSourceDocumentUploadItem {
  id: string;
  filename: string;
  status: string;
}

export interface BrandSourceDocumentsUploadResponse {
  documents: BrandSourceDocumentUploadItem[];
}

export interface BrandExtractedFact {
  id: string;
  projectId: string;
  sourceDocumentId?: string | null;
  targetSection: TargetSection;
  targetEntityType?: string | null;
  fieldName?: string | null;
  extractedValue?: unknown;
  sourceExcerpt?: string | null;
  confidence: number;
  status: FactStatus;
  aiReasoning?: string | null;
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
