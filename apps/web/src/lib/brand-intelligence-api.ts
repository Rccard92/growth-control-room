import type {
  BrandContextBundle,
  BrandIdentity,
  BrandIdentityApplyProposalRequest,
  BrandIdentityApplyProposalResponse,
  BrandIdentityImportResponse,
  BrandIntelligenceOverview,
  BrandKnowledgeScore,
  BrandProfile,
  BrandProfileApplyProposalRequest,
  BrandProfileEnrichRequest,
  BrandProfileEnrichResponse,
  BrandSafeClaims,
  BrandSafeClaimsApplyProposalRequest,
  BrandSafeClaimsApplyProposalResponse,
  BrandSafeClaimsImportResponse,
  BrandProductKnowledgeGeneral,
  BrandProductKnowledgeGeneralApplyProposalRequest,
  BrandProductKnowledgeGeneralApplyProposalResponse,
  BrandProductKnowledgeGeneralImportResponse,
  BrandProductKnowledgeItem,
  BrandProductKnowledgeItemFromShopifyRequest,
  BrandProductKnowledgeShopifyProductsResponse,
  BrandVisualIdentity,
  VisualApplyProposalRequest,
  VisualApplyProposalResponse,
  VisualExtractRequest,
  VisualExtractResponse,
} from "@gcr/shared";
import { apiFetch, apiUploadForm } from "./api";

export function getBrandIntelligenceOverview(
  projectId: string,
): Promise<BrandIntelligenceOverview> {
  return apiFetch<BrandIntelligenceOverview>(
    `/api/projects/${projectId}/brand-intelligence`,
  );
}

export function getBrandKnowledgeScore(projectId: string): Promise<BrandKnowledgeScore> {
  return apiFetch<BrandKnowledgeScore>(
    `/api/projects/${projectId}/brand-intelligence/score`,
  );
}

export function getBrandContext(projectId: string): Promise<BrandContextBundle> {
  return apiFetch<BrandContextBundle>(
    `/api/projects/${projectId}/brand-intelligence/context`,
  );
}

export function getBrandProfile(projectId: string): Promise<BrandProfile> {
  return apiFetch<BrandProfile>(`/api/projects/${projectId}/brand-intelligence/profile`);
}

export function updateBrandProfile(
  projectId: string,
  data: Partial<BrandProfile>,
): Promise<BrandProfile> {
  return apiFetch<BrandProfile>(`/api/projects/${projectId}/brand-intelligence/profile`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function enrichBrandProfile(
  projectId: string,
  data: BrandProfileEnrichRequest,
): Promise<BrandProfileEnrichResponse> {
  return apiFetch<BrandProfileEnrichResponse>(
    `/api/projects/${projectId}/brand-intelligence/profile/enrich`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function applyBrandProfileProposal(
  projectId: string,
  data: BrandProfileApplyProposalRequest,
): Promise<BrandProfile> {
  return apiFetch<BrandProfile>(
    `/api/projects/${projectId}/brand-intelligence/profile/apply-proposal`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function getBrandIdentity(projectId: string): Promise<BrandIdentity> {
  return apiFetch<BrandIdentity>(`/api/projects/${projectId}/brand-intelligence/identity`);
}

export function updateBrandIdentity(
  projectId: string,
  data: Partial<BrandIdentity>,
): Promise<BrandIdentity> {
  return apiFetch<BrandIdentity>(`/api/projects/${projectId}/brand-intelligence/identity`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function importBrandIdentityFromFile(
  projectId: string,
  file: File,
): Promise<BrandIdentityImportResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiUploadForm<BrandIdentityImportResponse>(
    `/api/projects/${projectId}/brand-intelligence/identity/import-file`,
    formData,
  );
}

export function applyBrandIdentityProposal(
  projectId: string,
  data: BrandIdentityApplyProposalRequest,
): Promise<BrandIdentityApplyProposalResponse> {
  return apiFetch<BrandIdentityApplyProposalResponse>(
    `/api/projects/${projectId}/brand-intelligence/identity/apply-proposal`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function getBrandVisualIdentity(projectId: string): Promise<BrandVisualIdentity> {
  return apiFetch<BrandVisualIdentity>(
    `/api/projects/${projectId}/brand-intelligence/visual-identity`,
  );
}

export function updateBrandVisualIdentity(
  projectId: string,
  data: Partial<BrandVisualIdentity>,
): Promise<BrandVisualIdentity> {
  return apiFetch<BrandVisualIdentity>(
    `/api/projects/${projectId}/brand-intelligence/visual-identity`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function extractVisualFromWebsite(
  projectId: string,
  data: VisualExtractRequest,
): Promise<VisualExtractResponse> {
  return apiFetch<VisualExtractResponse>(
    `/api/projects/${projectId}/brand-intelligence/visual-identity/extract-from-website`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function applyVisualProposal(
  projectId: string,
  data: VisualApplyProposalRequest,
): Promise<VisualApplyProposalResponse> {
  return apiFetch<VisualApplyProposalResponse>(
    `/api/projects/${projectId}/brand-intelligence/visual-identity/apply-proposal`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function getBrandSafeClaims(projectId: string): Promise<BrandSafeClaims> {
  return apiFetch<BrandSafeClaims>(`/api/projects/${projectId}/brand-intelligence/safe-claims`);
}

export function updateBrandSafeClaims(
  projectId: string,
  data: Partial<BrandSafeClaims>,
): Promise<BrandSafeClaims> {
  return apiFetch<BrandSafeClaims>(`/api/projects/${projectId}/brand-intelligence/safe-claims`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function importBrandSafeClaimsFromFile(
  projectId: string,
  file: File,
): Promise<BrandSafeClaimsImportResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiUploadForm<BrandSafeClaimsImportResponse>(
    `/api/projects/${projectId}/brand-intelligence/safe-claims/import-file`,
    formData,
  );
}

export function applyBrandSafeClaimsProposal(
  projectId: string,
  data: BrandSafeClaimsApplyProposalRequest,
): Promise<BrandSafeClaimsApplyProposalResponse> {
  return apiFetch<BrandSafeClaimsApplyProposalResponse>(
    `/api/projects/${projectId}/brand-intelligence/safe-claims/apply-proposal`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function getProductKnowledgeGeneral(
  projectId: string,
): Promise<BrandProductKnowledgeGeneral> {
  return apiFetch<BrandProductKnowledgeGeneral>(
    `/api/projects/${projectId}/brand-intelligence/product-knowledge/general`,
  );
}

export function updateProductKnowledgeGeneral(
  projectId: string,
  data: Partial<BrandProductKnowledgeGeneral>,
): Promise<BrandProductKnowledgeGeneral> {
  return apiFetch<BrandProductKnowledgeGeneral>(
    `/api/projects/${projectId}/brand-intelligence/product-knowledge/general`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function importProductKnowledgeGeneralFromFile(
  projectId: string,
  file: File,
): Promise<BrandProductKnowledgeGeneralImportResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiUploadForm<BrandProductKnowledgeGeneralImportResponse>(
    `/api/projects/${projectId}/brand-intelligence/product-knowledge/general/import-file`,
    formData,
  );
}

export function applyProductKnowledgeGeneralProposal(
  projectId: string,
  data: BrandProductKnowledgeGeneralApplyProposalRequest,
): Promise<BrandProductKnowledgeGeneralApplyProposalResponse> {
  return apiFetch<BrandProductKnowledgeGeneralApplyProposalResponse>(
    `/api/projects/${projectId}/brand-intelligence/product-knowledge/general/apply-proposal`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function getProductKnowledgeShopifyProducts(
  projectId: string,
): Promise<BrandProductKnowledgeShopifyProductsResponse> {
  return apiFetch<BrandProductKnowledgeShopifyProductsResponse>(
    `/api/projects/${projectId}/brand-intelligence/product-knowledge/shopify-products`,
  );
}

export function getProductKnowledgeItems(
  projectId: string,
): Promise<BrandProductKnowledgeItem[]> {
  return apiFetch<BrandProductKnowledgeItem[]>(
    `/api/projects/${projectId}/brand-intelligence/product-knowledge/items`,
  );
}

export function createProductKnowledgeItemFromShopify(
  projectId: string,
  data: BrandProductKnowledgeItemFromShopifyRequest,
): Promise<BrandProductKnowledgeItem> {
  return apiFetch<BrandProductKnowledgeItem>(
    `/api/projects/${projectId}/brand-intelligence/product-knowledge/items/from-shopify`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function updateProductKnowledgeItem(
  projectId: string,
  itemId: string,
  data: Partial<BrandProductKnowledgeItem>,
): Promise<BrandProductKnowledgeItem> {
  return apiFetch<BrandProductKnowledgeItem>(
    `/api/projects/${projectId}/brand-intelligence/product-knowledge/items/${itemId}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    },
  );
}

export function deleteProductKnowledgeItem(
  projectId: string,
  itemId: string,
): Promise<void> {
  return apiFetch<void>(
    `/api/projects/${projectId}/brand-intelligence/product-knowledge/items/${itemId}`,
    { method: "DELETE" },
  );
}
