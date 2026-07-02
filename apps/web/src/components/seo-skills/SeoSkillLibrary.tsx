import { useMemo, useState } from "react";
import type { SeoSkillProvider, SeoSkillRun } from "@gcr/shared";
import {
  useSeoSkillCatalog,
  useSeoSkillRun,
  useStartSeoSkillRun,
} from "../../hooks/useSeoSkills";
import { SeoSkillCard } from "./SeoSkillCard";
import { SeoSkillLauncher } from "./SeoSkillLauncher";
import {
  buildRunResultsSummary,
  formatSeoSkillRunError,
  formatSeoSkillRunStatus,
  getSkillDisabledReason,
  isSkillSelectable,
  matchesCategoryFilter,
  SEO_SKILL_CATEGORY_FILTERS,
  type SeoSkillCategoryFilterKey,
} from "./seo-skills-utils";

interface SeoSkillLibraryProps {
  projectId: string;
}

export function SeoSkillLibrary({ projectId }: SeoSkillLibraryProps) {
  const [categoryFilter, setCategoryFilter] = useState<SeoSkillCategoryFilterKey>("all");
  const [selectedSkills, setSelectedSkills] = useState<Set<string>>(new Set());
  const [provider, setProvider] = useState<SeoSkillProvider>("claude");
  const [targetUrl, setTargetUrl] = useState("");
  const [lastStartedRun, setLastStartedRun] = useState<SeoSkillRun | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const catalogQuery = useSeoSkillCatalog(projectId);
  const startMutation = useStartSeoSkillRun(projectId);
  const runQuery = useSeoSkillRun(
    projectId,
    lastStartedRun?.id,
    Boolean(lastStartedRun?.id),
  );

  const skills = catalogQuery.data?.skills ?? [];
  const counts = catalogQuery.data?.counts;

  const filteredSkills = useMemo(
    () => skills.filter((skill) => matchesCategoryFilter(skill, categoryFilter)),
    [skills, categoryFilter],
  );

  const skillsByKey = useMemo(
    () => new Map(skills.map((skill) => [skill.key, skill])),
    [skills],
  );

  const runStatus = runQuery.data?.run.status ?? lastStartedRun?.status;
  const runSummary = useMemo(
    () => buildRunResultsSummary(runQuery.data?.results, skillsByKey),
    [runQuery.data?.results, skillsByKey],
  );

  const handleToggleSkill = (skillKey: string) => {
    setSelectedSkills((prev) => {
      const next = new Set(prev);
      if (next.has(skillKey)) {
        next.delete(skillKey);
      } else {
        next.add(skillKey);
      }
      return next;
    });
  };

  const handleSubmit = async () => {
    setSubmitError(null);
    try {
      const result = await startMutation.mutateAsync({
        targetType: "url",
        url: targetUrl.trim(),
        selectedSkills: [...selectedSkills],
        provider,
      });
      setLastStartedRun(result.run);
    } catch (err) {
      setSubmitError(formatSeoSkillRunError(err));
    }
  };

  if (catalogQuery.isLoading) {
    return (
      <div className="seo-skill-library gcr-card">
        <div className="gcr-skeleton seo-skeleton-row" />
        <div className="gcr-skeleton seo-skeleton-row" />
        <div className="gcr-skeleton seo-skeleton-row" />
      </div>
    );
  }

  if (catalogQuery.isError) {
    const message =
      catalogQuery.error instanceof Error
        ? catalogQuery.error.message
        : "Impossibile caricare il catalogo skill.";
    return (
      <div className="seo-skill-library gcr-card">
        <div className="content-seo-banner content-seo-banner--warn">
          <p>{message}</p>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => void catalogQuery.refetch()}
          >
            Riprova
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="seo-skill-library">
      <header className="seo-skill-library__header">
        <h2 className="seo-skill-library__title">SEO Skill Library</h2>
        <p className="seo-skill-library__subtitle">
          Seleziona le skill Claude SEO da eseguire sul target scelto.
        </p>
      </header>

      {counts && (
        <div className="seo-skill-library__counts content-seo-kpi-strip content-seo-kpi-strip--compact">
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value">{counts.total}</span>
            <span className="content-seo-kpi__label">Totali</span>
          </div>
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value content-seo-kpi__value--good">
              {counts.available}
            </span>
            <span className="content-seo-kpi__label">Disponibili</span>
          </div>
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value content-seo-kpi__value--warn">
              {counts.needsConfig}
            </span>
            <span className="content-seo-kpi__label">Configurazione richiesta</span>
          </div>
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value">{counts.externalRequired}</span>
            <span className="content-seo-kpi__label">Esterne</span>
          </div>
          <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
            <span className="content-seo-kpi__value">{counts.planned}</span>
            <span className="content-seo-kpi__label">Pianificate</span>
          </div>
        </div>
      )}

      <div className="seo-skill-library__filters">
        {SEO_SKILL_CATEGORY_FILTERS.map((filter) => (
          <button
            key={filter.key}
            type="button"
            className={`seo-filter-chip ${categoryFilter === filter.key ? "seo-filter-chip--active" : ""}`}
            onClick={() => setCategoryFilter(filter.key)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      <div className="seo-skill-library__body">
        <div className="seo-skill-library__grid">
          {filteredSkills.length === 0 ? (
            <div className="seo-skill-library__empty gcr-card">
              Nessuna skill in questa categoria.
            </div>
          ) : (
            filteredSkills.map((skill) => {
              const selectable = isSkillSelectable(skill);
              return (
                <SeoSkillCard
                  key={skill.key}
                  skill={skill}
                  selected={selectedSkills.has(skill.key)}
                  disabled={!selectable}
                  disabledReason={getSkillDisabledReason(skill)}
                  onToggle={handleToggleSkill}
                />
              );
            })
          )}
        </div>

        <SeoSkillLauncher
          selectedSkillKeys={[...selectedSkills]}
          skills={skills}
          provider={provider}
          onProviderChange={setProvider}
          targetUrl={targetUrl}
          onTargetUrlChange={setTargetUrl}
          onSubmit={() => void handleSubmit()}
          isSubmitting={startMutation.isPending}
          submitError={submitError}
          lastStartedRun={lastStartedRun}
          runStatus={runStatus}
          runStatusLabel={formatSeoSkillRunStatus(runStatus)}
          runSummary={runSummary}
        />
      </div>
    </div>
  );
}
