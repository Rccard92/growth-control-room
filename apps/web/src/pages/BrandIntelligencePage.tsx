import { useState } from "react";
import { motion } from "framer-motion";
import { useParams } from "react-router-dom";
import type { BrandIntelligenceTab } from "@gcr/shared";
import { PageHeader } from "../components/PageHeader";
import { BrandIntelligenceOverviewPanel } from "../components/brand-intelligence/BrandIntelligenceOverview";
import { BrandProfilePanel } from "../components/brand-intelligence/BrandProfilePanel";
import { useBrandIntelligenceOverview } from "../hooks/useBrandIntelligence";
import { useProject } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";

const TABS: { id: BrandIntelligenceTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "profile", label: "Brand Profile" },
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
        <BrandIntelligenceOverviewPanel
          overview={overview}
          onGoToProfile={() => setTab("profile")}
        />
      )}

      {tab === "profile" && <BrandProfilePanel projectId={projectId} />}
    </motion.div>
  );
}
