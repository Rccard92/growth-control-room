import type { SeoAuditPreset } from "./seo-skill-presets";
import { formatAuditPresetLevel, formatAuditTargetType } from "./seo-skill-presets";

interface SeoAuditPresetCardProps {
  preset: SeoAuditPreset;
  selected: boolean;
  availableSkillCount: number;
  totalSkillCount: number;
  onSelect: (key: string) => void;
}

export function SeoAuditPresetCard({
  preset,
  selected,
  availableSkillCount,
  totalSkillCount,
  onSelect,
}: SeoAuditPresetCardProps) {
  return (
    <button
      type="button"
      className={`seo-audit-preset-card gcr-card seo-audit-preset-card--level-${preset.level} ${
        selected ? "seo-audit-preset-card--selected" : ""
      }`}
      onClick={() => onSelect(preset.key)}
      aria-pressed={selected}
    >
      <div className="seo-audit-preset-card__header">
        <span className="seo-audit-preset-card__badge">{preset.badge}</span>
        <span className={`seo-audit-preset-card__level seo-audit-preset-card__level--${preset.level}`}>
          {formatAuditPresetLevel(preset.level)}
        </span>
      </div>

      <h3 className="seo-audit-preset-card__title">{preset.title}</h3>
      <p className="seo-audit-preset-card__subtitle">{preset.subtitle}</p>
      <p className="seo-audit-preset-card__description">{preset.description}</p>

      <div className="seo-audit-preset-card__meta">
        <span>{formatAuditTargetType(preset.targetType)}</span>
        <span>
          {availableSkillCount}/{totalSkillCount} skill
        </span>
        <span>{preset.estimatedTimeLabel}</span>
      </div>

      <div className="seo-audit-preset-card__checks">
        <strong>Cosa controlla</strong>
        <ul>
          {preset.checksLabel.slice(0, 4).map((check) => (
            <li key={check}>{check}</li>
          ))}
        </ul>
      </div>

      {preset.recommendedFor.length > 0 && (
        <div className="seo-audit-preset-card__tags">
          {preset.recommendedFor.map((tag) => (
            <span key={tag} className="seo-audit-preset-card__tag">
              {tag}
            </span>
          ))}
        </div>
      )}

      <span className="seo-audit-preset-card__cta">
        {selected ? "Selezionato" : preset.ctaLabel}
      </span>
    </button>
  );
}
