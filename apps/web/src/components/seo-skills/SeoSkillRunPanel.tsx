import { motion } from "framer-motion";
import type { SeoSkillCatalogItem, SeoSkillRun } from "@gcr/shared";
import { useSeoSkillRun } from "../../hooks/useSeoSkills";
import { SeoAuditSummaryCard } from "./SeoAuditSummaryCard";
import { SeoSkillRunResultCard } from "./SeoSkillRunResultCard";
import {
  formatRunPanelHeadline,
  formatRunTimestamp,
  formatSeoSkillRunStatus,
} from "./seo-skills-utils";

interface SeoSkillRunPanelProps {
  projectId: string;
  runId: string;
  initialRun?: SeoSkillRun | null;
  catalogSkills?: SeoSkillCatalogItem[];
}

export function SeoSkillRunPanel({
  projectId,
  runId,
  initialRun,
  catalogSkills = [],
}: SeoSkillRunPanelProps) {
  const runQuery = useSeoSkillRun(projectId, runId, Boolean(runId));
  const run = runQuery.data?.run ?? initialRun;
  const results = runQuery.data?.results ?? [];

  if (runQuery.isLoading && !run) {
    return (
      <section className="seo-skill-run-panel gcr-card">
        <div className="gcr-skeleton seo-skeleton-row" />
        <div className="gcr-skeleton seo-skeleton-row" />
      </section>
    );
  }

  if (!run) {
    return null;
  }

  const headline = formatRunPanelHeadline(run.status);
  const statusLabel = formatSeoSkillRunStatus(run.status);

  return (
    <motion.section
      className="seo-skill-run-panel"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <header className="seo-skill-run-panel__header">
        <div>
          <h3 className="seo-skill-run-panel__title">{headline}</h3>
          <p className="seo-skill-run-panel__subtitle">Risultati analisi</p>
        </div>
        {typeof run.progressPercent === "number" && run.progressPercent < 100 && (
          <span className="seo-skill-run-panel__progress">{run.progressPercent}%</span>
        )}
      </header>

      <SeoAuditSummaryCard run={run} results={results} />

      <div className="seo-skill-run-panel__meta seo-skill-run-panel__meta--compact">
        <span>
          <strong>Stato:</strong> {statusLabel}
        </span>
        <span>
          <strong>Avviata:</strong> {formatRunTimestamp(run.startedAt ?? run.createdAt)}
        </span>
        <span>
          <strong>Completata:</strong> {formatRunTimestamp(run.completedAt)}
        </span>
      </div>

      {run.errorMessage && (
        <div className="seo-skill-run-panel__error">{run.errorMessage}</div>
      )}

      {results.length > 0 ? (
        <div className="seo-skill-run-panel__results">
          {results.map((result) => (
            <SeoSkillRunResultCard
              key={result.id}
              result={result}
              catalogSkills={catalogSkills}
            />
          ))}
        </div>
      ) : (
        <p className="seo-skill-run-panel__empty gcr-card">
          {run.status === "pending" || run.status === "running"
            ? "In attesa dei risultati delle skill…"
            : "Nessun risultato disponibile per questa run."}
        </p>
      )}
    </motion.section>
  );
}
