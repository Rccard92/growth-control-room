import type { SeoSkillCatalogItem, SeoSkillRun } from "@gcr/shared";
import { useSeoSkillRun } from "../../hooks/useSeoSkills";
import { SeoSkillRunResultCard } from "./SeoSkillRunResultCard";
import {
  buildRunPanelSummary,
  formatRunPanelHeadline,
  formatRunTimestamp,
  formatSeoSkillRunStatus,
  getSkillDisplayName,
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
  const summary = buildRunPanelSummary(results);

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
  const selectedSkillLabels = run.selectedSkills.map((key) =>
    getSkillDisplayName(key, catalogSkills),
  );

  return (
    <section className="seo-skill-run-panel gcr-card">
      <header className="seo-skill-run-panel__header">
        <div>
          <h3 className="seo-skill-run-panel__title">{headline}</h3>
          <p className="seo-skill-run-panel__subtitle">Risultati analisi</p>
        </div>
        {typeof run.progressPercent === "number" && run.progressPercent < 100 && (
          <span className="seo-skill-run-panel__progress">{run.progressPercent}%</span>
        )}
      </header>

      <div className="seo-skill-run-panel__meta">
        <p>
          <strong>Stato:</strong> {statusLabel}
        </p>
        <p>
          <strong>Provider:</strong> {run.provider}
        </p>
        {run.url && (
          <p>
            <strong>URL:</strong> {run.url}
          </p>
        )}
        <p>
          <strong>Avviata:</strong> {formatRunTimestamp(run.startedAt ?? run.createdAt)}
        </p>
        <p>
          <strong>Completata:</strong> {formatRunTimestamp(run.completedAt)}
        </p>
      </div>

      {selectedSkillLabels.length > 0 && (
        <div className="seo-skill-run-panel__skills">
          <strong>Skill selezionate:</strong>
          <ul>
            {selectedSkillLabels.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="seo-skill-run-panel__summary content-seo-kpi-strip content-seo-kpi-strip--compact">
        <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
          <span className="content-seo-kpi__value">{summary.total}</span>
          <span className="content-seo-kpi__label">Totali</span>
        </div>
        <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
          <span className="content-seo-kpi__value content-seo-kpi__value--good">
            {summary.completed}
          </span>
          <span className="content-seo-kpi__label">Completate</span>
        </div>
        <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
          <span className="content-seo-kpi__value content-seo-kpi__value--warn">
            {summary.failed}
          </span>
          <span className="content-seo-kpi__label">Fallite</span>
        </div>
        <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
          <span className="content-seo-kpi__value">{summary.running}</span>
          <span className="content-seo-kpi__label">In corso</span>
        </div>
        <div className="content-seo-kpi gcr-card content-seo-kpi--compact">
          <span className="content-seo-kpi__value">{summary.pending}</span>
          <span className="content-seo-kpi__label">In attesa</span>
        </div>
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
        <p className="seo-skill-run-panel__empty">
          {run.status === "pending" || run.status === "running"
            ? "In attesa dei risultati delle skill…"
            : "Nessun risultato disponibile per questa run."}
        </p>
      )}
    </section>
  );
}
