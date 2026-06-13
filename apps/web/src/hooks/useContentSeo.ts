import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  analyzeCollectionsSeo,
  analyzeProductsSeo,
  applyProposal,
  approveProposal,
  generateProposal,
  getCollectionAnalysis,
  getCollectionSeoDetail,
  getCollectionsSeo,
  getProductAnalysis,
  getProductSeoDetail,
  getProductsSeo,
  getProposal,
  listProposals,
  previewProposal,
  rejectProposal,
  saveManualProposal,
  syncCollectionSeo,
  syncProductSeo,
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

export function useProductSeoDetail(projectId: string, productId: string | null) {
  return useQuery({
    queryKey: queryKeys.contentSeo.productDetail(projectId, productId ?? ""),
    queryFn: () => getProductSeoDetail(projectId, productId!),
    enabled: Boolean(productId),
  });
}

export function useCollectionSeoDetail(projectId: string, collectionId: string | null) {
  return useQuery({
    queryKey: queryKeys.contentSeo.collectionDetail(projectId, collectionId ?? ""),
    queryFn: () => getCollectionSeoDetail(projectId, collectionId!),
    enabled: Boolean(collectionId),
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
      mode,
    }: {
      entityType: "product" | "collection";
      entityId: string;
      useAi?: boolean;
      mode?: string;
    }) => generateProposal(projectId, entityType, entityId, { useAi, mode }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.proposals(projectId) });
    },
  });
}

export function useSaveManualProposal(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      entityType,
      entityId,
      proposedValues,
    }: {
      entityType: "product" | "collection";
      entityId: string;
      proposedValues: Record<string, unknown>;
    }) => saveManualProposal(projectId, entityType, entityId, proposedValues),
    onSuccess: (_data, vars) => {
      void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.proposals(projectId) });
      if (vars.entityType === "product") {
        void qc.invalidateQueries({
          queryKey: queryKeys.contentSeo.productDetail(projectId, vars.entityId),
        });
      } else {
        void qc.invalidateQueries({
          queryKey: queryKeys.contentSeo.collectionDetail(projectId, vars.entityId),
        });
      }
    },
  });
}

export function usePreviewProposal(projectId: string, proposalId: string | null) {
  return useQuery({
    queryKey: queryKeys.contentSeo.proposalPreview(projectId, proposalId ?? ""),
    queryFn: () => previewProposal(projectId, proposalId!),
    enabled: Boolean(proposalId),
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
      mutationFn: ({
        proposalId,
      }: {
        proposalId: string;
        entityType?: "product" | "collection";
        entityId?: string;
      }) => applyProposal(projectId, proposalId),
      onSuccess: (_data, vars) => {
        invalidate();
        if (vars.entityType && vars.entityId) {
          if (vars.entityType === "product") {
            void qc.invalidateQueries({
              queryKey: queryKeys.contentSeo.productDetail(projectId, vars.entityId),
            });
          } else {
            void qc.invalidateQueries({
              queryKey: queryKeys.contentSeo.collectionDetail(projectId, vars.entityId),
            });
          }
        }
      },
    }),
  };
}

export function useSyncProductSeo(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (productId: string) => syncProductSeo(projectId, productId),
    onSuccess: (_data, productId) => {
      void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.products(projectId) });
      void qc.invalidateQueries({
        queryKey: queryKeys.contentSeo.productDetail(projectId, productId),
      });
    },
  });
}

export function useSyncCollectionSeo(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (collectionId: string) => syncCollectionSeo(projectId, collectionId),
    onSuccess: (_data, collectionId) => {
      void qc.invalidateQueries({ queryKey: queryKeys.contentSeo.collections(projectId) });
      void qc.invalidateQueries({
        queryKey: queryKeys.contentSeo.collectionDetail(projectId, collectionId),
      });
    },
  });
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
