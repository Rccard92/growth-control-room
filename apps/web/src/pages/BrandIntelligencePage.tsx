import { useState } from "react";
import { motion } from "framer-motion";
import { useParams } from "react-router-dom";
import type { BrandIntelligenceTab } from "@gcr/shared";
import { PageHeader } from "../components/PageHeader";
import { BrandAiContextPanel } from "../components/brand-intelligence/BrandAiContextPanel";
import { BrandIdentityPanel } from "../components/brand-intelligence/BrandIdentityPanel";
import { BrandIntelligenceOverviewPanel } from "../components/brand-intelligence/BrandIntelligenceOverview";
import { BrandProfilePanel } from "../components/brand-intelligence/BrandProfilePanel";
import { BrandProductKnowledgePanel } from "../components/brand-intelligence/BrandProductKnowledgePanel";
import { BrandSafeClaimsPanel } from "../components/brand-intelligence/BrandSafeClaimsPanel";
import { BrandVisualIdentityPanel } from "../components/brand-intelligence/BrandVisualIdentityPanel";
import { useBrandIntelligenceOverview } from "../hooks/useBrandIntelligence";
import { useProject } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";

const TABS: { id: BrandIntelligenceTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "profile", label: "Brand Profile" },
  { id: "identity", label: "Brand Identity" },
  { id: "visualIdentity", label: "Visual Identity" },
  { id: "safeClaims", label: "Safe Claims" },
  { id: "productKnowledge", label: "Product Knowledge" },
  { id: "aiContext", label: "AI Context" },
];

export function BrandIntelligencePage() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  const { data: project } = useProject(id);
  const { data: overview, isLoading } = useBrandIntelligenceOverview(projectId);
  const [tab, setTab] = useState<BrandIntelligenceTab>("overview");

  return (
    <motion.div
      className="brand-intelligence-page"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <PageHeader
        title="Brand Intelligence"
        subtitle="La fonte centrale del brand usata dai moduli AI."
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Brand Intelligence" },
        ]}
      />

      <nav className="bi-tabs" aria-label="Sezioni Brand Intelligence">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`bi-tabs__btn ${tab === t.id ? "bi-tabs__btn--active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {isLoading && tab === "overview" && (
        <p className="bi-panel__subtitle">Caricamento overview…</p>
      )}

      {tab === "overview" && overview && (
        <BrandIntelligenceOverviewPanel overview={overview} onOpenSection={setTab} />
      )}

      {tab === "profile" && <BrandProfilePanel projectId={projectId} />}
      {tab === "identity" && <BrandIdentityPanel projectId={projectId} />}
      {tab === "visualIdentity" && <BrandVisualIdentityPanel projectId={projectId} />}
      {tab === "safeClaims" && <BrandSafeClaimsPanel projectId={projectId} />}
      {tab === "productKnowledge" && <BrandProductKnowledgePanel projectId={projectId} />}
      {tab === "aiContext" && <BrandAiContextPanel projectId={projectId} />}
    </motion.div>
  );
}
