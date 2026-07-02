import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import type { SeoSkillProvider, SeoSkillRun } from "@gcr/shared";
import {
  useSeoSkillCatalog,
  useSeoSkillRun,
  useSeoSkillRuns,
  useStartSeoSkillRun,
} from "../../hooks/useSeoSkills";
import { SeoAuditConfigurator } from "./SeoAuditConfigurator";
import { SeoAuditPresetPicker } from "./SeoAuditPresetPicker";
import { SeoSkillCard } from "./SeoSkillCard";
import { SeoSkillRunHistory } from "./SeoSkillRunHistory";
import { SeoSkillRunPanel } from "./SeoSkillRunPanel";
import { getAuditPreset } from "./seo-skill-presets";
import {
  formatSeoSkillRunError,
  getSkillDisabledReason,
  matchesCategoryFilter,
  resolvePresetSkills,
  SEO_SKILL_CATEGORY_FILTERS,
  type SeoSkillCategoryFilterKey,
} from "./seo-skills-utils";

interface SeoSkillLibraryProps {
  projectId: string;
}

const AUDIT_FLOW_STEPS = [
  "Scegli audit",
  "Inserisci target",
  "Avvia analisi",
  "Correggi le priorità",
] as const;

export function SeoSkillLibrary({ projectId }: SeoSkillLibraryProps) {
  const [selectedPresetKey, setSelectedPresetKey] = useState("page_360");
  const [manualSkillKeys, setManualSkillKeys] = useState<Set<string>>(new Set());
  const [categoryFilter, setCategoryFilter] = useState<SeoSkillCategoryFilterKey>("all");
  const [provider, setProvider] = useState<SeoSkillProvider>("openai");
  const [targetUrl, setTargetUrl] = useState("");
  const [lastStartedRun, setLastStartedRun] = useState<SeoSkillRun | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const catalogQuery = useSeoSkillCatalog(projectId);
  const runsQuery = useSeoSkillRuns(projectId);
  const startMutation = useStartSeoSkillRun(projectId);
  const activeRunId = selectedRunId ?? lastStartedRun?.id ?? null;
  const runQuery = useSeoSkillRun(projectId, activeRunId ?? undefined, Boolean(activeRunId));

  const skills = catalogQuery.data?.skills ?? [];
  const preset = getAuditPreset(selectedPresetKey) ?? getAuditPreset("page_360")!;

  const resolvedSkills = useMemo(
    () => resolvePresetSkills(preset, skills, [...manualSkillKeys]),
    [preset, skills, manualSkillKeys],
  );

  const filteredSkills = useMemo(
    () => skills.filter((skill) => matchesCategoryFilter(skill, categoryFilter)),
    [skills, categoryFilter],
  );

  const recentRuns = useMemo(() => (runsQuery.data ?? []).slice(0, 5), [runsQuery.data]);

  const handleToggleManualSkill = (skillKey: string) => {
    setManualSkillKeys((prev) => {
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
    if (resolvedSkills.availableKeys.length === 0) {
      setSubmitError("Seleziona almeno una skill disponibile.");
      return;
    }
    try {
      const result = await startMutation.mutateAsync({
        targetType: preset.targetType,
        url: targetUrl.trim(),
        selectedSkills: resolvedSkills.availableKeys,
        provider,
      });
      setLastStartedRun(result.run);
      setSelectedRunId(result.run.id);
    } catch (err) {
      setSubmitError(formatSeoSkillRunError(err));
    }
  };

  if (catalogQuery.isLoading) {
    return (
      <div className="seo-audit-room gcr-card">
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
      <div className="seo-audit-room gcr-card">
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
    <div className="seo-audit-room">
      <header className="seo-audit-room__hero gcr-card">
        <h2 className="seo-audit-room__title">SEO Audit Control Room</h2>
        <p className="seo-audit-room__subtitle">
          Scegli un tipo di analisi, inserisci il target e ottieni problemi, priorità e azioni
          concrete.
        </p>
        <ol className="seo-audit-room__flow" aria-label="Flusso audit">
          {AUDIT_FLOW_STEPS.map((step, index) => (
            <li key={step} className="seo-audit-room__flow-step">
              <span className="seo-audit-room__flow-index">{index + 1}</span>
              <span>{step}</span>
              {index < AUDIT_FLOW_STEPS.length - 1 && (
                <span className="seo-audit-room__flow-arrow" aria-hidden>
                  →
                </span>
              )}
            </li>
          ))}
        </ol>
      </header>

      <div className="seo-audit-room__layout">
        <div className="seo-audit-room__main">
          {activeRunId && (
            <motion.div
              className="seo-audit-room__results"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
            >
              <SeoSkillRunPanel
                projectId={projectId}
                runId={activeRunId}
                initialRun={lastStartedRun}
                catalogSkills={skills}
              />
            </motion.div>
          )}

          <SeoAuditPresetPicker
            catalog={skills}
            selectedKey={selectedPresetKey}
            onSelect={setSelectedPresetKey}
            compact={Boolean(activeRunId)}
          />

          {selectedPresetKey !== "custom" && (
            <details className="seo-audit-room__tech-catalog">
              <summary>Vedi tutte le skill tecniche</summary>
              <div className="seo-audit-room__tech-filters">
                {SEO_SKILL_CATEGORY_FILTERS.map((filter) => (
                  <button
                    key={filter.key}
                    type="button"
                    className={`seo-filter-chip ${
                      categoryFilter === filter.key ? "seo-filter-chip--active" : ""
                    }`}
                    onClick={() => setCategoryFilter(filter.key)}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
              <div className="seo-audit-room__tech-grid">
                {filteredSkills.map((skill) => {
                  const included = preset.includedSkills.includes(skill.key);
                  return (
                    <SeoSkillCard
                      key={skill.key}
                      skill={skill}
                      selected={included}
                      disabled
                      disabledReason={
                        included
                          ? "Inclusa nel preset selezionato"
                          : getSkillDisabledReason(skill) ?? "Non inclusa nel preset"
                      }
                      onToggle={() => undefined}
                    />
                  );
                })}
              </div>
            </details>
          )}
        </div>

        <aside className="seo-audit-room__sidebar">
          <SeoAuditConfigurator
            preset={preset}
            catalog={skills}
            manualSkillKeys={manualSkillKeys}
            onToggleManualSkill={handleToggleManualSkill}
            categoryFilter={categoryFilter}
            onCategoryFilterChange={setCategoryFilter}
            provider={provider}
            onProviderChange={setProvider}
            targetUrl={targetUrl}
            onTargetUrlChange={setTargetUrl}
            onSubmit={() => void handleSubmit()}
            isSubmitting={startMutation.isPending}
            submitError={submitError}
            lastStartedRun={lastStartedRun}
            runStatus={runQuery.data?.run.status ?? lastStartedRun?.status}
          />

          {recentRuns.length > 0 && (
            <SeoSkillRunHistory
              runs={recentRuns}
              selectedRunId={activeRunId}
              onSelectRun={setSelectedRunId}
            />
          )}
        </aside>
      </div>
    </div>
  );
}
