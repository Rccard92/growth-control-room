import type { SeoSkillCatalogItem } from "@gcr/shared";
import {
  formatSkillCategory,
  formatSkillRuntime,
  formatSkillStatus,
  formatDefaultProvider,
} from "./seo-skills-utils";

interface SeoSkillCardProps {
  skill: SeoSkillCatalogItem;
  selected: boolean;
  disabled: boolean;
  disabledReason?: string | null;
  onToggle: (skillKey: string) => void;
}

export function SeoSkillCard({
  skill,
  selected,
  disabled,
  disabledReason,
  onToggle,
}: SeoSkillCardProps) {
  const handleClick = () => {
    if (disabled) return;
    onToggle(skill.key);
  };

  return (
    <button
      type="button"
      className={`seo-skill-card gcr-card ${selected ? "seo-skill-card--selected" : ""} ${disabled ? "seo-skill-card--disabled" : ""}`}
      onClick={handleClick}
      disabled={disabled}
      aria-pressed={selected}
      aria-disabled={disabled}
    >
      <div className="seo-skill-card__header">
        <div className="seo-skill-card__title-row">
          <span className={`seo-skill-card__checkbox ${selected ? "seo-skill-card__checkbox--checked" : ""}`} />
          <h3 className="seo-skill-card__title">{skill.label}</h3>
        </div>
        <span className="seo-skill-card__category">{formatSkillCategory(skill.category)}</span>
      </div>

      <p className="seo-skill-card__description">{skill.description}</p>

      <div className="seo-skill-card__badges">
        <span className={`seo-skill-badge seo-skill-badge--${skill.status}`}>
          {formatSkillStatus(skill.status)}
        </span>
        <span className={`seo-skill-badge seo-skill-badge--runtime seo-skill-badge--runtime-${skill.runtime}`}>
          {formatSkillRuntime(skill.runtime)}
        </span>
      </div>

      <p className="seo-skill-card__default-provider">{formatDefaultProvider(String(skill.defaultProvider))}</p>

      <div className="seo-skill-card__meta">
        <span className="seo-skill-card__meta-label">Comando</span>
        <code className="seo-skill-card__command">{skill.upstreamCommand}</code>
      </div>

      {skill.requiredIntegrations.length > 0 && (
        <div className="seo-skill-card__integrations">
          <span className="seo-skill-card__meta-label">Integrazioni richieste</span>
          <div className="seo-skill-card__chip-row">
            {skill.requiredIntegrations.map((item) => (
              <span key={item} className="seo-skill-card__chip seo-skill-card__chip--required">
                {item}
              </span>
            ))}
          </div>
        </div>
      )}

      {skill.optionalIntegrations.length > 0 && (
        <div className="seo-skill-card__integrations">
          <span className="seo-skill-card__meta-label">Integrazioni opzionali</span>
          <div className="seo-skill-card__chip-row">
            {skill.optionalIntegrations.map((item) => (
              <span key={item} className="seo-skill-card__chip">
                {item}
              </span>
            ))}
          </div>
        </div>
      )}

      {disabled && disabledReason && (
        <p className="seo-skill-card__disabled-reason">{disabledReason}</p>
      )}
    </button>
  );
}
