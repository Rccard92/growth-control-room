import { SeoEntityEditPanel } from "./SeoEntityEditPanel";

interface SeoEntityEditDrawerProps {
  open: boolean;
  onClose: () => void;
  projectId: string;
  entityType: "product" | "collection";
  entityId: string;
  title: string;
  productDetail?: import("@gcr/shared").SeoProductDetailResponse;
  collectionDetail?: import("@gcr/shared").SeoCollectionDetailResponse;
  detailLoading?: boolean;
  detailError?: boolean;
  detailErrorMessage?: string;
  openaiConfigured: boolean;
  writeProductsAvailable: boolean;
  onDetailRefresh?: () => void;
}

export function SeoEntityEditDrawer(props: SeoEntityEditDrawerProps) {
  return <SeoEntityEditPanel {...props} embedded={false} />;
}
