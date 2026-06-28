import type { EditorialArticlePayload } from "@gcr/shared";
import { analyzeEditorialQuality } from "./editorial-quality-utils";

interface EditorialQualityPanelProps {
  article: EditorialArticlePayload;
}

export function EditorialQualityPanel({ article }: EditorialQualityPanelProps) {
  const quality = analyzeEditorialQuality(article);

  return (
    <aside className="editorial-quality-panel gcr-card">
      <h4 className="gcr-card__title">Qualità editoriale</h4>
      <dl className="editorial-quality-panel__list">
        <div>
          <dt>Skill usata</dt>
          <dd>
            {quality.skillPackUsed}
            {quality.skillPackVersion !== "—" ? ` (${quality.skillPackVersion})` : ""}
          </dd>
        </div>
        <div>
          <dt>Grassetti</dt>
          <dd>
            {quality.strongCount}
            {quality.strongInRange ? " (target 6–9)" : " (fuori target 6–9)"}
          </dd>
        </div>
        <div>
          <dt>Liste</dt>
          <dd>{quality.listCount > 0 ? "Sì" : "No"}</dd>
        </div>
        <div>
          <dt>Box evidenza</dt>
          <dd>{quality.boxCount > 0 ? "Sì" : "No"}</dd>
        </div>
        <div>
          <dt>Wrapper body</dt>
          <dd>{quality.hasBodyWrapper ? "Sì" : "No"}</dd>
        </div>
        <div>
          <dt>CTA</dt>
          <dd>{quality.hasCta ? (quality.hasCtaBox ? "Sì (box visivo)" : "Sì") : "No"}</dd>
        </div>
        <div>
          <dt>Paragrafi lunghi</dt>
          <dd>{quality.hasLongParagraphs ? "Sì" : "No"}</dd>
        </div>
      </dl>
      {quality.safeClaimFlags.length > 0 && (
        <div className="editorial-quality-panel__safe-claims">
          <span className="gcr-field__label">Safe Claims</span>
          <ul>
            {quality.safeClaimFlags.map((flag) => (
              <li key={`${flag.phrase}-${flag.reason}`}>
                Possibile claim da verificare: «{flag.phrase}»
              </li>
            ))}
          </ul>
        </div>
      )}
      {quality.warnings.length > 0 && (
        <div className="editorial-quality-panel__warnings">
          <span className="gcr-field__label">Avvisi</span>
          <ul>
            {quality.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
}
