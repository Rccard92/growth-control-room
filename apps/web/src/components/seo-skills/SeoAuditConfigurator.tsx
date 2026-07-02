import type { SeoSkillCatalogItem, SeoSkillProvider, SeoSkillRun } from "@gcr/shared";
import { SeoSkillCard } from "./SeoSkillCard";
import type { SeoAuditPreset } from "./seo-skill-presets";
import {
  canSubmitLauncher,
  formatSeoSkillRunStatus,
  getSkillDisabledReason,
  getSkillDisplayName,
  isSkillSelectable,
  matchesCategoryFilter,
  resolvePresetSkills,
  SEO_SKILL_CATEGORY_FILTERS,
  type SeoSkillCategoryFilterKey,
} from "./seo-skills-utils";

interface SeoAuditConfiguratorProps {
  preset: SeoAuditPreset;
  catalog: SeoSkillCatalogItem[];
  manualSkillKeys: Set<string>;
  onToggleManualSkill: (skillKey: string) => void;
  categoryFilter: SeoSkillCategoryFilterKey;
  onCategoryFilterChange: (filter: SeoSkillCategoryFilterKey) => void;
  provider: SeoSkillProvider;
  onProviderChange: (provider: SeoSkillProvider) => void;
  targetUrl: string;
  onTargetUrlChange: (url: string) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
  submitError?: string | null;
  lastStartedRun?: SeoSkillRun | null;
  runStatus?: string | null;
}

export function SeoAuditConfigurator({
  preset,
  catalog,
  manualSkillKeys,
  onToggleManualSkill,
  categoryFilter,
  onCategoryFilterChange,
  provider,
  onProviderChange,
  targetUrl,
  onTargetUrlChange,
  onSubmit,
  isSubmitting,
  submitError,
  lastStartedRun,
  runStatus,
}: SeoAuditConfiguratorProps) {
  const resolved = resolvePresetSkills(preset, catalog, [...manualSkillKeys]);
  const isCustom = preset.key === "custom";
  const filteredSkills = catalog.filter((skill) => matchesCategoryFilter(skill, categoryFilter));

  const canSubmit = canSubmitLauncher({
    selectedCount: resolved.availableKeys.length,
    targetUrl,
    isSubmitting,
  });

  const displayStatus = formatSeoSkillRunStatus(runStatus ?? lastStartedRun?.status);

  return (
    <aside className="seo-audit-configurator gcr-card">
      <header className="seo-audit-configurator__header">
        <h3 className="seo-audit-configurator__title">Configura analisi</h3>
        <p className="seo-audit-configurator__preset-name">{preset.title}</p>
        {preset.microcopy && (
          <p className="seo-audit-configurator__microcopy">{preset.microcopy}</p>
        )}
      </header>

      <div className="seo-audit-configurator__field">
        <label className="seo-audit-configurator__label" htmlFor="seo-audit-provider">
          Provider
        </label>
        <select
          id="seo-audit-provider"
          className="gcr-input"
          value={provider}
          onChange={(event) => onProviderChange(event.target.value as SeoSkillProvider)}
        >
          <option value="openai">OpenAI</option>
          <option value="claude">Claude</option>
        </select>
        <p className="seo-audit-configurator__hint">
          {provider === "openai"
            ? "OpenAI: consigliato per output strutturati e report puliti."
            : "Claude: utile per analisi strategiche e qualitative, se configurato."}
        </p>
      </div>

      <div className="seo-audit-configurator__field">
        <label className="seo-audit-configurator__label" htmlFor="seo-audit-target-url">
          URL target
        </label>
        <input
          id="seo-audit-target-url"
          className="gcr-input"
          type="url"
          placeholder="https://example.com/pagina"
          value={targetUrl}
          onChange={(event) => onTargetUrlChange(event.target.value)}
        />
      </div>

      <div className="seo-audit-configurator__field">
        <span className="seo-audit-configurator__label">Skill incluse</span>
        {resolved.availableKeys.length === 0 ? (
          <p className="seo-audit-configurator__empty">
            {isCustom
              ? "Seleziona almeno una skill disponibile."
              : "Nessuna skill disponibile per questo preset."}
          </p>
        ) : (
          <div className="seo-audit-configurator__skill-chips">
            {resolved.availableKeys.map((key) => (
              <span key={key} className="seo-audit-configurator__chip seo-audit-configurator__chip--available">
                {getSkillDisplayName(key, catalog)}
              </span>
            ))}
          </div>
        )}
        {resolved.unavailableKeys.length > 0 && (
          <>
            <div className="seo-audit-configurator__warning content-seo-banner content-seo-banner--warn">
              Alcune skill del preset non sono ancora disponibili e verranno saltate.
            </div>
            <div className="seo-audit-configurator__skill-chips">
              {resolved.unavailableKeys.map((key) => (
                <span
                  key={key}
                  className="seo-audit-configurator__chip seo-audit-configurator__chip--unavailable"
                  title="Non disponibile"
                >
                  {getSkillDisplayName(key, catalog)}
                </span>
              ))}
            </div>
          </>
        )}
      </div>

      {isCustom && (
        <details className="seo-audit-configurator__custom-catalog" open>
          <summary>Seleziona skill manualmente</summary>
          <div className="seo-audit-configurator__filters">
            {SEO_SKILL_CATEGORY_FILTERS.map((filter) => (
              <button
                key={filter.key}
                type="button"
                className={`seo-filter-chip ${
                  categoryFilter === filter.key ? "seo-filter-chip--active" : ""
                }`}
                onClick={() => onCategoryFilterChange(filter.key)}
              >
                {filter.label}
              </button>
            ))}
          </div>
          <div className="seo-audit-configurator__skill-grid">
            {filteredSkills.map((skill) => {
              const selectable = isSkillSelectable(skill);
              return (
                <SeoSkillCard
                  key={skill.key}
                  skill={skill}
                  selected={manualSkillKeys.has(skill.key)}
                  disabled={!selectable}
                  disabledReason={getSkillDisabledReason(skill)}
                  onToggle={onToggleManualSkill}
                />
              );
            })}
          </div>
        </details>
      )}

      {submitError && (
        <div className="seo-audit-configurator__error content-seo-banner content-seo-banner--warn">
          {submitError}
        </div>
      )}

      {lastStartedRun && (
        <div className="seo-audit-configurator__feedback">
          <strong>Analisi avviata</strong>
          <p>Stato: {displayStatus}</p>
        </div>
      )}

      <button
        type="button"
        className="gcr-btn gcr-btn--primary seo-audit-configurator__submit"
        disabled={!canSubmit}
        onClick={onSubmit}
      >
        {isSubmitting ? "Avvio in corso…" : preset.ctaLabel}
      </button>
    </aside>
  );
}
