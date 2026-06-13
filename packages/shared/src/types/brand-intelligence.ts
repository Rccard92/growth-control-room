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
