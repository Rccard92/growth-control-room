import type { SeoSkillFindingView } from "./seo-skills-utils";

interface SeoSkillFindingsListProps {
  findings: SeoSkillFindingView[];
}

export function SeoSkillFindingsList({ findings }: SeoSkillFindingsListProps) {
  if (!findings.length) {
    return <p className="seo-skill-result-section__empty">Nessun problema rilevato.</p>;
  }

  return (
    <ul className="seo-skill-findings-list">
      {findings.map((finding, index) => (
        <li
          key={`${finding.title}-${index}`}
          className={`seo-skill-finding seo-skill-finding--${finding.severity}`}
        >
          <div className="seo-skill-finding__badges">
            <span className={`seo-skill-badge seo-skill-badge--severity-${finding.severity}`}>
              {finding.severityLabel}
            </span>
            <span className="seo-skill-badge seo-skill-badge--priority">
              Priorità {finding.priorityLabel}
            </span>
            {finding.area && <span className="seo-skill-finding__area">{finding.area}</span>}
          </div>
          <h5 className="seo-skill-finding__title">{finding.title}</h5>
          {finding.whyItMatters && (
            <p className="seo-skill-finding__meta">
              <strong>Perché conta:</strong> {finding.whyItMatters}
            </p>
          )}
          {finding.description && (
            <p className="seo-skill-finding__meta">
              <strong>Cosa succede:</strong> {finding.description}
            </p>
          )}
          {finding.evidence && (
            <p className="seo-skill-finding__meta">
              <strong>Evidenza:</strong> {finding.evidence}
            </p>
          )}
          {finding.recommendation && (
            <p className="seo-skill-finding__meta">
              <strong>Come risolvere:</strong> {finding.recommendation}
            </p>
          )}
          {finding.howToValidate && (
            <p className="seo-skill-finding__meta">
              <strong>Come verificare:</strong> {finding.howToValidate}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}
