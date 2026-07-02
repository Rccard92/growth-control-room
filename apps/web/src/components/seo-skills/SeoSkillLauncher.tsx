import type { SeoSkillCatalogItem, SeoSkillProvider, SeoSkillRun } from "@gcr/shared";
import { canSubmitLauncher } from "./seo-skills-utils";

interface SeoSkillLauncherProps {
  selectedSkillKeys: string[];
  skills: SeoSkillCatalogItem[];
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

export function SeoSkillLauncher({
  selectedSkillKeys,
  skills,
  provider,
  onProviderChange,
  targetUrl,
  onTargetUrlChange,
  onSubmit,
  isSubmitting,
  submitError,
  lastStartedRun,
  runStatus,
}: SeoSkillLauncherProps) {
  const selectedLabels = skills
    .filter((skill) => selectedSkillKeys.includes(skill.key))
    .map((skill) => skill.label);

  const canSubmit = canSubmitLauncher({
    selectedCount: selectedSkillKeys.length,
    targetUrl,
    isSubmitting,
  });

  return (
    <aside className="seo-skill-launcher gcr-card">
      <div className="seo-skill-launcher__header">
        <h3 className="seo-skill-launcher__title">Avvia analisi</h3>
        <p className="seo-skill-launcher__subtitle">
          Seleziona le skill e inserisci la URL da analizzare.
        </p>
      </div>

      <div className="seo-skill-launcher__field">
        <label className="seo-skill-launcher__label" htmlFor="seo-skill-provider">
          Provider
        </label>
        <select
          id="seo-skill-provider"
          className="gcr-input"
          value={provider}
          onChange={(event) => onProviderChange(event.target.value as SeoSkillProvider)}
        >
          <option value="claude">Claude</option>
          <option value="openai">OpenAI</option>
        </select>
      </div>

      <div className="seo-skill-launcher__field">
        <span className="seo-skill-launcher__label">Target</span>
        <div className="seo-skill-launcher__target-types">
          <span className="seo-skill-launcher__target-type seo-skill-launcher__target-type--active">
            URL
          </span>
          <span className="seo-skill-launcher__target-type seo-skill-launcher__target-type--soon">
            Prodotto Shopify — in arrivo
          </span>
          <span className="seo-skill-launcher__target-type seo-skill-launcher__target-type--soon">
            Collezione Shopify — in arrivo
          </span>
        </div>
      </div>

      <div className="seo-skill-launcher__field">
        <label className="seo-skill-launcher__label" htmlFor="seo-skill-target-url">
          URL target
        </label>
        <input
          id="seo-skill-target-url"
          className="gcr-input"
          type="url"
          placeholder="https://example.com/pagina"
          value={targetUrl}
          onChange={(event) => onTargetUrlChange(event.target.value)}
        />
      </div>

      <div className="seo-skill-launcher__field">
        <span className="seo-skill-launcher__label">
          Skill selezionate ({selectedSkillKeys.length})
        </span>
        {selectedLabels.length === 0 ? (
          <p className="seo-skill-launcher__empty">Nessuna skill selezionata.</p>
        ) : (
          <ul className="seo-skill-launcher__selected-list">
            {selectedLabels.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        )}
      </div>

      {submitError && (
        <div className="seo-skill-launcher__feedback seo-skill-launcher__feedback--error">
          {submitError}
        </div>
      )}

      {lastStartedRun && (
        <div className="seo-skill-launcher__feedback seo-skill-launcher__feedback--success">
          <strong>Run avviata</strong>
          <p>ID: {lastStartedRun.id}</p>
          <p>Stato: {runStatus ?? lastStartedRun.status}</p>
        </div>
      )}

      <button
        type="button"
        className="gcr-btn gcr-btn--primary seo-skill-launcher__submit"
        disabled={!canSubmit}
        onClick={onSubmit}
      >
        {isSubmitting ? "Avvio in corso…" : "Avvia analisi"}
      </button>
    </aside>
  );
}
