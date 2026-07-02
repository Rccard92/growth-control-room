import type { SeoSkillRecommendationView } from "./seo-skills-utils";

interface SeoSkillRecommendationsListProps {
  recommendations: SeoSkillRecommendationView[];
}

export function SeoSkillRecommendationsList({
  recommendations,
}: SeoSkillRecommendationsListProps) {
  if (!recommendations.length) {
    return <p className="seo-skill-result-section__empty">Nessuna raccomandazione.</p>;
  }

  return (
    <ul className="seo-skill-recommendations-list">
      {recommendations.map((item, index) => (
        <li key={`${item.title}-${index}`} className="seo-skill-recommendation">
          <h5 className="seo-skill-recommendation__title">{item.title}</h5>
          {item.description && (
            <p className="seo-skill-recommendation__description">{item.description}</p>
          )}
          <div className="seo-skill-recommendation__meta">
            <span>Priorità: {item.priorityLabel}</span>
            <span>Impatto: {item.impactLabel}</span>
            <span>Sforzo: {item.effortLabel}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}
