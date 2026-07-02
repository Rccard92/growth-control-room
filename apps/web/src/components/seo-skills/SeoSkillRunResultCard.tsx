import type { SeoSkillCatalogItem, SeoSkillRunResult } from "@gcr/shared";
import { SeoSkillArtifactsPanel } from "./SeoSkillArtifactsPanel";
import { SeoSkillFindingsList } from "./SeoSkillFindingsList";
import { SeoSkillRecommendationsList } from "./SeoSkillRecommendationsList";
import { SeoSkillTasksList } from "./SeoSkillTasksList";
import {
  formatSeoSkillResultStatus,
  getResultArtifacts,
  getResultFindings,
  getResultRecommendations,
  getResultScore,
  getResultSummary,
  getResultTasks,
  getSkillDisplayName,
} from "./seo-skills-utils";

interface SeoSkillRunResultCardProps {
  result: SeoSkillRunResult;
  catalogSkills?: SeoSkillCatalogItem[];
}

export function SeoSkillRunResultCard({ result, catalogSkills }: SeoSkillRunResultCardProps) {
  const skillLabel = getSkillDisplayName(result.skillKey, catalogSkills);
  const statusLabel = formatSeoSkillResultStatus(result.status);
  const score = getResultScore(result);
  const summary = getResultSummary(result);
  const findings = getResultFindings(result);
  const recommendations = getResultRecommendations(result);
  const tasks = getResultTasks(result);
  const artifacts = getResultArtifacts(result);
  const isFailed = result.status === "failed";
  const isCompleted = result.status === "completed";

  return (
    <article
      className={`seo-skill-result-card gcr-card ${
        isFailed
          ? "seo-skill-result-card--failed"
          : isCompleted
            ? "seo-skill-result-card--completed"
            : ""
      }`}
    >
      <header className="seo-skill-result-card__header">
        <div>
          <h4 className="seo-skill-result-card__title">{skillLabel}</h4>
          <p className="seo-skill-result-card__status">Stato: {statusLabel}</p>
        </div>
        {score !== null && (
          <div className="seo-skill-result-card__score">
            <span className="seo-skill-result-card__score-value">{score}</span>
            <span className="seo-skill-result-card__score-label">Score</span>
          </div>
        )}
      </header>

      {isFailed && result.errorMessage && (
        <div className="seo-skill-result-card__error">{result.errorMessage}</div>
      )}

      <details className="seo-skill-result-section seo-skill-result-section--priority" open={tasks.length > 0}>
        <summary>Azioni prioritarie ({tasks.length})</summary>
        <SeoSkillTasksList tasks={tasks} />
      </details>

      <details className="seo-skill-result-section" open={findings.length > 0}>
        <summary>Problemi rilevati ({findings.length})</summary>
        <SeoSkillFindingsList findings={findings} />
      </details>

      <details className="seo-skill-result-section" open={recommendations.length > 0}>
        <summary>Raccomandazioni ({recommendations.length})</summary>
        <SeoSkillRecommendationsList recommendations={recommendations} />
      </details>

      <details className="seo-skill-result-section">
        <summary>Artifacts</summary>
        <SeoSkillArtifactsPanel artifacts={artifacts} />
      </details>

      {summary && (
        <details className="seo-skill-result-section">
          <summary>Sintesi</summary>
          <p className="seo-skill-result-card__summary">{summary}</p>
        </details>
      )}

      {result.rawOutput && (
        <details className="seo-skill-result-section seo-skill-debug-json">
          <summary>Debug JSON</summary>
          <pre>{JSON.stringify(result.rawOutput, null, 2)}</pre>
        </details>
      )}
    </article>
  );
}
