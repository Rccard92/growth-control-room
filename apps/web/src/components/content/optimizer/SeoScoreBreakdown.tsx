import type { SeoScoreBreakdown, SeoSkillMeta } from "@gcr/shared";
import { breakdownFieldLabel } from "./SeoMissingFieldBadge";

interface SeoScoreBreakdownProps {
  scoreTotal?: number | null;
  scoreBreakdown?: SeoScoreBreakdown | null;
  title?: string;
  skillMeta?: SeoSkillMeta | null;
}

const DEFAULT_CATEGORIES = [
  "Regole prodotto",
  "Regole metadata",
  "Regole immagini",
  "Regole contenuto",
  "Regole Shopify/GCR",
];

export function SeoScoreBreakdown({
  scoreTotal,
  scoreBreakdown,
  title = "Come è calcolato lo score",
  skillMeta,
}: SeoScoreBreakdownProps) {
  if (!scoreBreakdown || Object.keys(scoreBreakdown).length === 0) {
    return (
      <p className="shopify-empty-copy">
        Esegui l&apos;analisi SEO per vedere il breakdown del punteggio.
      </p>
    );
  }

  return (
    <section className="seo-score-breakdown">
      <h4>{title}</h4>
      <p className="seo-score-breakdown__subtitle">
        Lo score deriva da:{" "}
        {(skillMeta?.scoreRuleCategories ?? DEFAULT_CATEGORIES).join(" · ")}
      </p>
      {scoreTotal != null && (
        <p className="seo-score-breakdown__total">
          Score totale: <strong>{scoreTotal}</strong> / 100
        </p>
      )}
      <ul className="seo-score-breakdown__list">
        {Object.entries(scoreBreakdown).map(([key, item]) => {
          const pct = item.max > 0 ? Math.round((item.score / item.max) * 100) : 0;
          return (
            <li key={key} className="seo-score-breakdown__item">
              <div className="seo-score-breakdown__row">
                <span>{breakdownFieldLabel(key)}</span>
                <span>
                  {item.score}/{item.max}
                </span>
              </div>
              <div className="seo-score-breakdown__bar">
                <div
                  className="seo-score-breakdown__bar-fill"
                  style={{ width: `${pct}%` }}
                />
              </div>
              {item.issues.length > 0 && (
                <ul className="seo-score-breakdown__issues">
                  {item.issues.map((issue, idx) => (
                    <li key={`${key}-${idx}`}>{String(issue.message ?? issue.code ?? "")}</li>
                  ))}
                </ul>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
