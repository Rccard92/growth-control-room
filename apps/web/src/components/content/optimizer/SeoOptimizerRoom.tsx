import { useState } from "react";
import type { SeoOptimizationProposal, SeoOptimizerTab } from "@gcr/shared";
import { StatusBadge } from "../../StatusBadge";
import { EntitySeoTable, type EntityFilter } from "./EntitySeoTable";
import { SeoEntityEditDrawer } from "./SeoEntityEditDrawer";
import {
  useAnalyzeCollectionsSeo,
  useAnalyzeProductsSeo,
  useCollectionSeoDetail,
  useCollectionsSeo,
  useProductSeoDetail,
  useProductsSeo,
  useProposalsSeo,
  useSeoOptimizerSync,
} from "../../../hooks/useContentSeo";
import { useShopifyScopes } from "../../../hooks/useShopify";

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
  const [editEntity, setEditEntity] = useState<{
    type: "product" | "collection";
    id: string;
    title: string;
  } | null>(null);

  const { data: productsData, isLoading: productsLoading } = useProductsSeo(projectId, connected);
  const { data: collectionsData, isLoading: collectionsLoading } = useCollectionsSeo(
    projectId,
    connected,
  );
  const { data: proposalsData } = useProposalsSeo(projectId, connected);
  const shopifyScopesQuery = useShopifyScopes(projectId, connected);

  const syncMutation = useSeoOptimizerSync(projectId);
  const analyzeProductsMutation = useAnalyzeProductsSeo(projectId);
  const analyzeCollectionsMutation = useAnalyzeCollectionsSeo(projectId);

  const productDetail = useProductSeoDetail(
    projectId,
    editEntity?.type === "product" ? editEntity.id : null,
  );
  const collectionDetail = useCollectionSeoDetail(
    projectId,
    editEntity?.type === "collection" ? editEntity.id : null,
  );

  const openaiConfigured = productsData?.openaiConfigured ?? collectionsData?.openaiConfigured ?? false;
  const writeProductsAvailable =
    shopifyScopesQuery.data?.canWriteProducts ??
    productsData?.writeProductsAvailable ??
    collectionsData?.writeProductsAvailable ??
    false;

  const handleOpenEdit = (entityType: "product" | "collection", entityId: string) => {
    const title =
      entityType === "product"
        ? productsData?.items.find((p) => p.id === entityId)?.title
        : collectionsData?.items.find((c) => c.id === entityId)?.title;
    setEditEntity({
      type: entityType,
      id: entityId,
      title: title ?? "Modifica SEO",
    });
  };

  const refreshDetail = () => {
    if (editEntity?.type === "product") {
      void productDetail.refetch();
    } else if (editEntity?.type === "collection") {
      void collectionDetail.refetch();
    }
  };

  const activeDetailQuery =
    editEntity?.type === "product" ? productDetail : collectionDetail;
  const detailErrorMessage =
    activeDetailQuery.isError && activeDetailQuery.error instanceof Error
      ? activeDetailQuery.error.message
      : activeDetailQuery.isError
        ? "Impossibile caricare i dati SEO."
        : undefined;

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

      {(syncMutation.isSuccess ||
        analyzeProductsMutation.isSuccess ||
        analyzeCollectionsMutation.isSuccess) && (
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
              onEdit={(id) => handleOpenEdit("product", id)}
              editLoadingId={
                editEntity?.type === "product" && productDetail.isFetching
                  ? editEntity.id
                  : null
              }
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
              onEdit={(id) => handleOpenEdit("collection", id)}
              editLoadingId={
                editEntity?.type === "collection" && collectionDetail.isFetching
                  ? editEntity.id
                  : null
              }
            />
          )}
        </div>
      )}

      {tab === "proposals" && (
        <div className="gcr-card content-seo-panel">
          <ProposalList
            proposals={proposalsData?.items ?? []}
            onOpen={(p) =>
              setEditEntity({
                type: p.entityType,
                id: p.entityId,
                title: p.entityGid,
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

      <SeoEntityEditDrawer
        open={Boolean(editEntity)}
        onClose={() => setEditEntity(null)}
        projectId={projectId}
        entityType={editEntity?.type ?? "product"}
        entityId={editEntity?.id ?? ""}
        title={editEntity?.title ?? ""}
        productDetail={productDetail.data}
        collectionDetail={collectionDetail.data}
        detailLoading={productDetail.isLoading || collectionDetail.isLoading}
        detailError={productDetail.isError || collectionDetail.isError}
        detailErrorMessage={detailErrorMessage}
        openaiConfigured={openaiConfigured}
        writeProductsAvailable={writeProductsAvailable}
        onDetailRefresh={refreshDetail}
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
    return (
      <p className="shopify-empty-copy">
        Nessuna proposta. Apri Modifica da tab Prodotti o Categorie.
      </p>
    );
  }
  return (
    <ul className="shopify-seo-list">
      {proposals.slice(0, 10).map((p) => (
        <li key={p.id} className="shopify-seo-list__item">
          <span>
            {p.entityType} · {p.status} · {p.riskLevel}
          </span>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => onOpen(p)}
          >
            Apri
          </button>
        </li>
      ))}
    </ul>
  );
}
