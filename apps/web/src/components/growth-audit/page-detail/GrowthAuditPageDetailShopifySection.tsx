import type { GrowthAuditPage } from "@gcr/shared";
import { SeoEntityEditPanel } from "../../content/optimizer/SeoEntityEditPanel";
import {
  useCollectionSeoDetail,
  useCollectionsSeo,
  useProductSeoDetail,
  useProductsSeo,
} from "../../../hooks/useContentSeo";
import {
  getGrowthAuditSourceEntityTypeLabel,
  isGrowthAuditPageShopifyLinked,
  mapGrowthAuditPageToSeoEntity,
} from "../../../lib/growth-audit-utils";

interface GrowthAuditPageDetailShopifySectionProps {
  projectId: string;
  page: GrowthAuditPage;
}

export function GrowthAuditPageDetailShopifySection({
  projectId,
  page,
}: GrowthAuditPageDetailShopifySectionProps) {
  const mappedSeoEntity = mapGrowthAuditPageToSeoEntity(page);
  const shopifyLinked = isGrowthAuditPageShopifyLinked(page);

  const productDetailQuery = useProductSeoDetail(
    projectId,
    mappedSeoEntity?.entityType === "product" ? mappedSeoEntity.entityId : null,
  );
  const collectionDetailQuery = useCollectionSeoDetail(
    projectId,
    mappedSeoEntity?.entityType === "collection" ? mappedSeoEntity.entityId : null,
  );
  const productsSeoQuery = useProductsSeo(
    projectId,
    Boolean(mappedSeoEntity?.entityType === "product"),
  );
  const collectionsSeoQuery = useCollectionsSeo(
    projectId,
    Boolean(mappedSeoEntity?.entityType === "collection"),
  );

  const seoDetailLoading =
    mappedSeoEntity?.entityType === "product"
      ? productDetailQuery.isLoading
      : collectionDetailQuery.isLoading;

  const seoDetailError =
    mappedSeoEntity?.entityType === "product"
      ? productDetailQuery.isError
      : collectionDetailQuery.isError;

  const openaiConfigured =
    productsSeoQuery.data?.openaiConfigured ??
    collectionsSeoQuery.data?.openaiConfigured ??
    false;
  const writeProductsAvailable =
    productsSeoQuery.data?.writeProductsAvailable ??
    collectionsSeoQuery.data?.writeProductsAvailable ??
    false;

  return (
    <section
      id="shopify-edit"
      className="growth-audit-page-detail__section growth-audit-page-detail__shopify"
    >
      <h2 className="growth-audit-page-detail__section-title">Modifica Shopify</h2>
      {mappedSeoEntity ? (
        <>
          {shopifyLinked && (
            <p className="growth-audit-page-detail__shopify-meta">
              {getGrowthAuditSourceEntityTypeLabel(page.sourceEntityType)}
              {page.sourceEntityTitle ? ` · ${page.sourceEntityTitle}` : ""}
            </p>
          )}
          <div className="growth-audit-page-detail__shopify-editor">
            <SeoEntityEditPanel
              embedded
              projectId={projectId}
              entityType={mappedSeoEntity.entityType}
              entityId={mappedSeoEntity.entityId}
              title={page.sourceEntityTitle ?? page.title ?? page.url}
              productDetail={
                mappedSeoEntity.entityType === "product" ? productDetailQuery.data : undefined
              }
              collectionDetail={
                mappedSeoEntity.entityType === "collection"
                  ? collectionDetailQuery.data
                  : undefined
              }
              detailLoading={seoDetailLoading}
              detailError={seoDetailError}
              detailErrorMessage={
                seoDetailError ? "Impossibile caricare i dati SEO dell'entità." : undefined
              }
              openaiConfigured={openaiConfigured}
              writeProductsAvailable={writeProductsAvailable}
              onDetailRefresh={() => {
                if (mappedSeoEntity.entityType === "product") {
                  void productDetailQuery.refetch();
                } else {
                  void collectionDetailQuery.refetch();
                }
              }}
            />
          </div>
          <p className="growth-audit-page-detail__shopify-callout">
            Dopo aver applicato le modifiche, riscansiona la pagina per aggiornare lo score
            tecnico.
          </p>
        </>
      ) : (
        <p className="growth-audit-page-detail__empty">
          Questa pagina non è collegata a un&apos;entità Shopify modificabile.
        </p>
      )}
    </section>
  );
}
