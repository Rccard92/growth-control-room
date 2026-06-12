import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  analyzeCollectionsSeo,
  analyzeProductsSeo,
  applyProposal,
  approveProposal,
  generateProposal,
  getCollectionAnalysis,
  getCollectionsSeo,
  getProductAnalysis,
  getProductsSeo,
  getProposal,
  listProposals,
  rejectProposal,
  syncSeoOptimizer,
} from "../lib/content-api";
import { queryKeys } from "../lib/queryKeys";

export function useProductsSeo(projectId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.contentSeo.products(projectId ?? ""),
    queryFn: () => getProductsSeo(projectId!),
    enabled: Boolean(projectId) && enabled,
  });
}

export function useCollectionsSeo(projectId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.contentSeo.collections(projectId ?? ""),
    queryFn: () => getCollectionsSeo(projectId!),
    enabled: Boolean(projectId) && enabled,
  });
}

export function useProposalsSeo(projectId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.contentSeo.proposals(projectId ?? ""),
    queryFn: () => listProposals(projectId!),
    enabled: Boolean(projectId) && enabled,
  });
}

export function useSeoOptimizerSync(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => syncSeoOptimizer(projectId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.products(projectId) });
      void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.collections(projectId) });
    },
  });
}

export function useAnalyzeProductsSeo(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => analyzeProductsSeo(projectId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.products(projectId) });
    },
  });
}

export function useAnalyzeCollectionsSeo(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => analyzeCollectionsSeo(projectId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.collections(projectId) });
    },
  });
}

export function useGenerateProposal(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      entityType,
      entityId,
      useAi,
    }: {
      entityType: "product" | "collection";
      entityId: string;
      useAi?: boolean;
    }) => generateProposal(projectId, entityType, entityId, useAi),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.proposals(projectId) });
      void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.products(projectId) });
      void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.collections(projectId) });
    },
  });
}

export function useProposalActions(projectId: string) {
  const qc = useQueryClient();
  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.proposals(projectId) });
    void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.products(projectId) });
    void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.collections(projectId) });
  };
  return {
    approve: useMutation({
      mutationFn: (proposalId: string) => approveProposal(projectId, proposalId),
      onSuccess: invalidate,
    }),
    reject: useMutation({
      mutationFn: (proposalId: string) => rejectProposal(projectId, proposalId),
      onSuccess: invalidate,
    }),
    apply: useMutation({
      mutationFn: (proposalId: string) => applyProposal(projectId, proposalId),
      onSuccess: invalidate,
    }),
  };
}

export function useProductAnalysis(projectId: string, entityId: string | null) {
  return useQuery({
    queryKey: queryKeys.contentSeo.productAnalysis(projectId, entityId ?? ""),
    queryFn: () => getProductAnalysis(projectId, entityId!),
    enabled: Boolean(entityId),
  });
}

export function useCollectionAnalysis(projectId: string, entityId: string | null) {
  return useQuery({
    queryKey: queryKeys.contentSeo.collectionAnalysis(projectId, entityId ?? ""),
    queryFn: () => getCollectionAnalysis(projectId, entityId!),
    enabled: Boolean(entityId),
  });
}

export function useProposalDetail(projectId: string, proposalId: string | null) {
  return useQuery({
    queryKey: queryKeys.contentSeo.proposalDetail(projectId, proposalId ?? ""),
    queryFn: () => getProposal(projectId, proposalId!),
    enabled: Boolean(proposalId),
  });
}
