import { BrandIntelligenceImportPanel } from "../components/brand-intelligence/BrandIntelligenceImportPanel";
import { useParams } from "react-router-dom";

export function BrandIntelligenceImportPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  if (!projectId) return null;
  return <BrandIntelligenceImportPanel projectId={projectId} />;
}
