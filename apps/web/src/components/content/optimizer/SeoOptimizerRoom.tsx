import { useState } from "react";
import type { SeoOptimizerTab } from "@gcr/shared";
import { StatusBadge } from "../../StatusBadge";
import { EntitySeoTable, type EntityFilter } from "./EntitySeoTable";
import { SeoEntityEditDrawer } from "./SeoEntityEditDrawer";
import { ContentSeoOptimizerKpi, averageScore } from "./ContentSeoOptimizerKpi";
import { ContentSeoToast } from "./ContentSeoToast";
import type { ContentSeoFeedback } from "./ContentSeoActionBar";
import {
  useCollectionSeoDetail,
  useCollectionsSeo,
  useContentSeoDashboard,
  useProductSeoDetail,
  useProductsSeo,
} from "../../../hooks/useContentSeo";
import { useShopifyScopes } from "../../../hooks/useShopify";

const TABS: { id: SeoOptimizerTab; label: string; comingSoon?: boolean }[] = [
  { id: "products", label: "Prodotti" },
  { id: "collections", label: "Categorie" },
  { id: "editorial", label: "Blog & Ricette", comingSoon: true },
];

interface SeoOptimizerRoomProps {
  projectId: string;
  connected: boolean;
  feedback: ContentSeoFeedback | null;
  onDismissFeedback: () => void;
}

export function SeoOptimizerRoom({
  projectId,
  connected,
  feedback,
  onDismissFeedback,
}: SeoOptimizerRoomProps) {
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
  const { data: dashboardData, isLoading: dashboardLoading } = useContentSeoDashboard(
    projectId,
    connected,
  );
  const shopifyScopesQuery = useShopifyScopes(projectId, connected);

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

  const products = productsData?.items ?? [];
  const collections = collectionsData?.items ?? [];
  const summary = dashboardData?.summary;

  const handleOpenEdit = (entityType: "product" | "collection", entityId: string) => {
    const title =
      entityType === "product"
        ? products.find((p) => p.id === entityId)?.title
        : collections.find((c) => c.id === entityId)?.title;
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
      <ContentSeoOptimizerKpi
        productsCount={products.length}
        averageProductScore={averageScore(products)}
        collectionsCount={collections.length}
        averageCollectionScore={averageScore(collections)}
        criticalIssues={summary?.criticalIssues ?? 0}
        missingFieldsCount={
          (summary?.productsWithoutMeta ?? 0) + (summary?.collectionsWeak ?? 0)
        }
        loading={productsLoading || collectionsLoading || dashboardLoading}
      />

      <ContentSeoToast feedback={feedback} onDismiss={onDismissFeedback} />

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
        <div className="gcr-card content-seo-panel content-seo-panel--compact">
          {productsLoading ? (
            <div className="gcr-skeleton seo-skeleton-row" />
          ) : (
            <EntitySeoTable
              items={products}
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
        <div className="gcr-card content-seo-panel content-seo-panel--compact">
          <p className="content-seo-collections-hint">
            Categorie Shopify = Collections (non tag prodotto né product type).
          </p>
          {collectionsLoading ? (
            <div className="gcr-skeleton seo-skeleton-row" />
          ) : (
            <EntitySeoTable
              items={collections}
              mode="collection"
              filter={collectionFilter}
              onFilterChange={setCollectionFilter}
              onEdit={(id) => handleOpenEdit("collection", id)}
              editLoadingId={
                editEntity?.type === "collection" && collectionDetail.isFetching
                  ? editEntity.id
                  : null
              }
              emptyMessage="Nessuna collection Shopify sincronizzata. Clicca 'Sincronizza Shopify'."
            />
          )}
        </div>
      )}

      {tab === "editorial" && (
        <div className="gcr-card content-seo-empty content-seo-empty--compact">
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
