import type {
  BrandContextBundle,
  BrandIdentity,
  BrandIntelligenceOverview,
  BrandKnowledgeScore,
  BrandProfile,
  BrandProfileApplyProposalRequest,
  BrandProfileEnrichRequest,
  BrandProfileEnrichResponse,
  BrandVisualIdentity,
  VisualApplyProposalRequest,
  VisualApplyProposalResponse,
  VisualExtractRequest,
  VisualExtractResponse,
} from "@gcr/shared";
import { apiFetch } from "./api";

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
