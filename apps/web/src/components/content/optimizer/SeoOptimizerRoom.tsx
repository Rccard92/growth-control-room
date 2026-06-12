import { useState } from "react";
import type { SeoOptimizationProposal, SeoOptimizerTab } from "@gcr/shared";
import { StatusBadge } from "../../StatusBadge";
import { EntitySeoTable, type EntityFilter } from "./EntitySeoTable";
import { SeoDetailDrawer } from "./SeoDetailDrawer";
import {
  useAnalyzeCollectionsSeo,
  useAnalyzeProductsSeo,
  useCollectionAnalysis,
  useCollectionsSeo,
  useGenerateProposal,
  useProductAnalysis,
  useProductsSeo,
  useProposalActions,
  useProposalDetail,
  useProposalsSeo,
  useSeoOptimizerSync,
} from "../../../hooks/useContentSeo";

const TABS: { id: SeoOptimizerTab; label: string; comingSoon?: boolean }[] = [
  { id: "products", label: "Prodotti" },
  { id: "collections", label: "Categorie" },
  { id: "proposals", label: "Proposte" },
  { id: "editorial", label: "Blog & Ricette", comingSoon: true },
];

interface SeoOptimizerRoomProps {
  projectId: string;
  connected: boolean;
}

export function SeoOptimizerRoom({ projectId, connected }: SeoOptimizerRoomProps) {
  const [tab, setTab] = useState<SeoOptimizerTab>("products");
  const [productFilter, setProductFilter] = useState<EntityFilter>("all");
  const [collectionFilter, setCollectionFilter] = useState<EntityFilter>("all");
  const [detailEntity, setDetailEntity] = useState<{
    type: "product" | "collection";
    id: string;
    title: string;
    proposalId?: string;
  } | null>(null);

  const { data: productsData, isLoading: productsLoading } = useProductsSeo(projectId, connected);
  const { data: collectionsData, isLoading: collectionsLoading } = useCollectionsSeo(
    projectId,
    connected,
  );
  const { data: proposalsData } = useProposalsSeo(projectId, connected);

  const syncMutation = useSeoOptimizerSync(projectId);
  const analyzeProductsMutation = useAnalyzeProductsSeo(projectId);
  const analyzeCollectionsMutation = useAnalyzeCollectionsSeo(projectId);
  const generateMutation = useGenerateProposal(projectId);
  const proposalActions = useProposalActions(projectId);

  const productAnalysis = useProductAnalysis(
    projectId,
    detailEntity?.type === "product" ? detailEntity.id : null,
  );
  const collectionAnalysis = useCollectionAnalysis(
    projectId,
    detailEntity?.type === "collection" ? detailEntity.id : null,
  );
  const proposalDetail = useProposalDetail(projectId, detailEntity?.proposalId ?? null);

  const openaiConfigured = productsData?.openaiConfigured ?? collectionsData?.openaiConfigured ?? false;
  const writeProductsAvailable =
    productsData?.writeProductsAvailable ?? collectionsData?.writeProductsAvailable ?? false;

  const analysis =
    detailEntity?.type === "product" ? productAnalysis.data : collectionAnalysis.data;

  const handleGenerate = (entityType: "product" | "collection", entityId: string) => {
    generateMutation.mutate(
      { entityType, entityId, useAi: true },
      {
        onSuccess: (proposal) => {
          const title =
            entityType === "product"
              ? productsData?.items.find((p) => p.id === entityId)?.title
              : collectionsData?.items.find((c) => c.id === entityId)?.title;
          setDetailEntity({
            type: entityType,
            id: entityId,
            title: title ?? "Dettaglio",
            proposalId: proposal.id,
          });
        },
      },
    );
  };

  return (
    <>
      <div className="seo-optimizer-header">
        <div>
          <p className="gcr-card__label">SEO Optimizer</p>
          <h2 className="content-seo-header__title">Product & Collection SEO Optimizer</h2>
          <p className="content-seo-header__subtitle">
            Migliora titoli, SEO title, meta description, handle e alt immagini prima della
            pubblicazione.
          </p>
        </div>
        <div className="content-seo-header__actions">
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            disabled={syncMutation.isPending}
            onClick={() => syncMutation.mutate()}
          >
            {syncMutation.isPending ? "Sync…" : "Sincronizza contenuti Shopify"}
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            disabled={analyzeProductsMutation.isPending}
            onClick={() => analyzeProductsMutation.mutate()}
          >
            {analyzeProductsMutation.isPending ? "Analisi…" : "Analizza prodotti"}
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={analyzeCollectionsMutation.isPending}
            onClick={() => analyzeCollectionsMutation.mutate()}
          >
            {analyzeCollectionsMutation.isPending ? "Analisi…" : "Analizza categorie"}
          </button>
        </div>
      </div>

      {!openaiConfigured && (
        <div className="content-seo-banner content-seo-banner--warn">
          AI non configurata. Aggiungi OPENAI_API_KEY per generare proposte automatiche. L&apos;analisi
          rule-based funziona comunque.
        </div>
      )}

      {!writeProductsAvailable && (
        <div className="content-seo-banner content-seo-banner--warn">
          Per applicare le modifiche su Shopify serve autorizzare write_products.
        </div>
      )}

      {(syncMutation.isSuccess || analyzeProductsMutation.isSuccess || analyzeCollectionsMutation.isSuccess) && (
        <div className="content-seo-banner content-seo-banner--success">
          {syncMutation.isSuccess &&
            `Sync: ${syncMutation.data.productsSynced} prodotti, ${syncMutation.data.collectionsSynced} categorie.`}
          {analyzeProductsMutation.isSuccess &&
            ` Prodotti analizzati: ${analyzeProductsMutation.data.productsAnalyzed}.`}
          {analyzeCollectionsMutation.isSuccess &&
            ` Categorie analizzate: ${analyzeCollectionsMutation.data.collectionsAnalyzed}.`}
        </div>
      )}

      <div className="seo-optimizer-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`seo-optimizer-tab ${tab === t.id ? "seo-optimizer-tab--active" : ""}`}
            disabled={t.comingSoon}
            onClick={() => !t.comingSoon && setTab(t.id)}
          >
            {t.label}
            {t.comingSoon && <StatusBadge variant="coming_soon" />}
          </button>
        ))}
      </div>

      {tab === "products" && (
        <div className="gcr-card content-seo-panel">
          {productsLoading ? (
            <div className="gcr-skeleton seo-skeleton-row" />
          ) : (
            <EntitySeoTable
              items={productsData?.items ?? []}
              mode="product"
              filter={productFilter}
              onFilterChange={setProductFilter}
              openaiConfigured={openaiConfigured}
              generateLoadingId={
                generateMutation.isPending ? generateMutation.variables?.entityId ?? null : null
              }
              onGenerate={(id) => handleGenerate("product", id)}
              onDetails={(id) => {
                const item = productsData?.items.find((p) => p.id === id);
                setDetailEntity({ type: "product", id, title: item?.title ?? "Prodotto" });
              }}
            />
          )}
        </div>
      )}

      {tab === "collections" && (
        <div className="gcr-card content-seo-panel">
          {collectionsLoading ? (
            <div className="gcr-skeleton seo-skeleton-row" />
          ) : (
            <EntitySeoTable
              items={collectionsData?.items ?? []}
              mode="collection"
              filter={collectionFilter}
              onFilterChange={setCollectionFilter}
              openaiConfigured={openaiConfigured}
              generateLoadingId={
                generateMutation.isPending ? generateMutation.variables?.entityId ?? null : null
              }
              onGenerate={(id) => handleGenerate("collection", id)}
              onDetails={(id) => {
                const item = collectionsData?.items.find((c) => c.id === id);
                setDetailEntity({ type: "collection", id, title: item?.title ?? "Categoria" });
              }}
            />
          )}
        </div>
      )}

      {tab === "proposals" && (
        <div className="gcr-card content-seo-panel">
          <ProposalList
            proposals={proposalsData?.items ?? []}
            onOpen={(p) =>
              setDetailEntity({
                type: p.entityType,
                id: p.entityId,
                title: p.entityGid,
                proposalId: p.id,
              })
            }
          />
        </div>
      )}

      {tab === "editorial" && (
        <div className="gcr-card content-seo-empty">
          <h3 className="gcr-card__title">Blog & Ricette</h3>
          <p className="gcr-card__description">Modulo Editorial SEO in arrivo.</p>
          <StatusBadge variant="coming_soon" />
        </div>
      )}

      <SeoDetailDrawer
        open={Boolean(detailEntity)}
        onClose={() => setDetailEntity(null)}
        title={detailEntity?.title ?? ""}
        analysis={analysis}
        proposal={proposalDetail.data}
        writeProductsAvailable={writeProductsAvailable}
        actionLoading={
          proposalActions.approve.isPending ||
          proposalActions.reject.isPending ||
          proposalActions.apply.isPending
        }
        onApprove={() => {
          if (detailEntity?.proposalId) {
            proposalActions.approve.mutate(detailEntity.proposalId);
          }
        }}
        onReject={() => {
          if (detailEntity?.proposalId) {
            proposalActions.reject.mutate(detailEntity.proposalId);
          }
        }}
        onApply={() => {
          if (detailEntity?.proposalId) {
            proposalActions.apply.mutate(detailEntity.proposalId, {
              onSuccess: (res) => {
                if (res.message && !res.applied) {
                  alert(res.message);
                }
              },
            });
          }
        }}
      />
    </>
  );
}

function ProposalList({
  proposals,
  onOpen,
}: {
  proposals: SeoOptimizationProposal[];
  onOpen: (p: SeoOptimizationProposal) => void;
}) {
  if (proposals.length === 0) {
    return <p className="shopify-empty-copy">Nessuna proposta. Genera da tab Prodotti o Categorie.</p>;
  }
  return (
    <ul className="shopify-seo-list">
      {proposals.slice(0, 10).map((p) => (
        <li key={p.id} className="shopify-seo-list__item">
          <span>{p.entityType} · {p.status} · {p.riskLevel}</span>
          <button type="button" className="gcr-btn gcr-btn--secondary gcr-btn--sm" onClick={() => onOpen(p)}>
            Apri
          </button>
        </li>
      ))}
    </ul>
  );
}
