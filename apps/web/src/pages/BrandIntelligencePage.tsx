import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Outlet, useLocation, useNavigate, useParams } from "react-router-dom";
import type { BrandIntelligenceTab } from "@gcr/shared";
import { PageHeader } from "../components/PageHeader";
import { BrandIntelligenceOverviewPanel } from "../components/brand-intelligence/BrandIntelligenceOverview";
import { BrandWizard } from "../components/brand-intelligence/BrandWizard";
import { BrandProfilePanel } from "../components/brand-intelligence/BrandProfilePanel";
import { BrandVoicePanel } from "../components/brand-intelligence/BrandVoicePanel";
import { BrandProductsPanel } from "../components/brand-intelligence/BrandProductsPanel";
import { BrandAudiencePanel } from "../components/brand-intelligence/BrandAudiencePanel";
import { BrandClaimsPanel } from "../components/brand-intelligence/BrandClaimsPanel";
import { BrandSeoStrategyPanel } from "../components/brand-intelligence/BrandSeoStrategyPanel";
import { BrandContentPillarsPanel } from "../components/brand-intelligence/BrandContentPillarsPanel";
import { BrandGuardrailsPanel } from "../components/brand-intelligence/BrandGuardrailsPanel";
import { BrandAssetsPanel } from "../components/brand-intelligence/BrandAssetsPanel";
import { BrandSourcesPanel } from "../components/brand-intelligence/BrandSourcesPanel";
import { useBrandIntelligenceOverview } from "../hooks/useBrandIntelligence";
import { useProject } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";

const TABS: { id: BrandIntelligenceTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "wizard", label: "Wizard" },
  { id: "import", label: "Import AI" },
  { id: "profile", label: "Profile" },
  { id: "voice", label: "Voice" },
  { id: "products", label: "Products" },
  { id: "audience", label: "Audience" },
  { id: "claims", label: "Claims" },
  { id: "seo", label: "SEO" },
  { id: "pillars", label: "Pillars" },
  { id: "guardrails", label: "Guardrails" },
  { id: "assets", label: "Assets" },
  { id: "sources", label: "Documenti" },
];

export function BrandIntelligencePage() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  const navigate = useNavigate();
  const location = useLocation();
  const { data: project } = useProject(id);
  const { data: overview, isLoading } = useBrandIntelligenceOverview(projectId);
  const [tab, setTab] = useState<BrandIntelligenceTab>("overview");

  const isImportRoute = location.pathname.endsWith("/import");

  useEffect(() => {
    if (isImportRoute) {
      setTab("import");
    }
  }, [isImportRoute]);

  function goToTab(next: BrandIntelligenceTab) {
    setTab(next);
    if (next === "import" && id) {
      navigate(APP_ROUTES.projectBrandIntelligenceImport(id));
    } else if (isImportRoute && id) {
      navigate(APP_ROUTES.projectBrandIntelligence(id));
    }
  }

  return (
    <motion.div
      className="brand-intelligence-page"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <PageHeader
        title="Brand Intelligence"
        subtitle="Profilo brand, voice, compliance e contesto AI per contenuti on-brand."
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
            onClick={() => goToTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {isImportRoute ? (
        <Outlet />
      ) : (
        <>
          {isLoading && tab === "overview" && (
            <p className="bi-panel__subtitle">Caricamento overview…</p>
          )}

          {tab === "overview" && overview && (
            <BrandIntelligenceOverviewPanel
              overview={overview}
              onStartWizard={() => goToTab("wizard")}
              onStartImport={() => goToTab("import")}
              onGoToTab={goToTab}
            />
          )}

          {tab === "wizard" && projectId && (
            <BrandWizard projectId={projectId} onComplete={() => goToTab("overview")} />
          )}

          {tab === "profile" && projectId && <BrandProfilePanel projectId={projectId} />}
          {tab === "voice" && projectId && <BrandVoicePanel projectId={projectId} />}
          {tab === "products" && projectId && <BrandProductsPanel projectId={projectId} />}
          {tab === "audience" && projectId && <BrandAudiencePanel projectId={projectId} />}
          {tab === "claims" && projectId && <BrandClaimsPanel projectId={projectId} />}
          {tab === "seo" && projectId && <BrandSeoStrategyPanel projectId={projectId} />}
          {tab === "pillars" && projectId && <BrandContentPillarsPanel projectId={projectId} />}
          {tab === "guardrails" && projectId && <BrandGuardrailsPanel projectId={projectId} />}
          {tab === "assets" && projectId && <BrandAssetsPanel projectId={projectId} />}
          {tab === "sources" && projectId && (
            <BrandSourcesPanel projectId={projectId} onGoToImport={() => goToTab("import")} />
          )}
        </>
      )}
    </motion.div>
  );
}
