import type { SeoSkillRun } from "@gcr/shared";
import { formatRunTimestamp, formatSeoSkillRunStatus } from "./seo-skills-utils";

interface SeoSkillRunHistoryProps {
  runs: SeoSkillRun[];
  selectedRunId?: string | null;
  onSelectRun: (runId: string) => void;
}

export function SeoSkillRunHistory({
  runs,
  selectedRunId,
  onSelectRun,
}: SeoSkillRunHistoryProps) {
  if (!runs.length) return null;

  return (
    <section className="seo-skill-run-history gcr-card">
      <h3 className="seo-skill-run-history__title">Ultime analisi</h3>
      <ul className="seo-skill-run-history__list">
        {runs.map((run) => (
          <li key={run.id}>
            <button
              type="button"
              className={`seo-skill-run-history__item ${
                selectedRunId === run.id ? "seo-skill-run-history__item--active" : ""
              }`}
              onClick={() => onSelectRun(run.id)}
            >
              <span className="seo-skill-run-history__date">
                {formatRunTimestamp(run.startedAt ?? run.createdAt)}
              </span>
              <span className="seo-skill-run-history__status">
                {formatSeoSkillRunStatus(run.status)}
              </span>
              <span className="seo-skill-run-history__url">{run.url ?? "—"}</span>
              <span className="seo-skill-run-history__count">
                {run.selectedSkills.length} skill
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
