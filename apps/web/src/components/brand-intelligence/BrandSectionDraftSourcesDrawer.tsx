import type { BrandExtractedFact, BrandExternalSource, BrandSectionDraftListItem } from "@gcr/shared";
import { BrandExtractedFactsReview } from "./BrandExtractedFactsReview";

interface BrandSectionDraftSourcesDrawerProps {
  open: boolean;
  onClose: () => void;
  draft: BrandSectionDraftListItem;
  facts: BrandExtractedFact[];
  externalSources?: BrandExternalSource[];
}

const TYPE_LABELS: Record<string, string> = {
  website: "Sito web",
  instagram: "Instagram",
  facebook: "Facebook",
  tiktok: "TikTok",
  youtube: "YouTube",
  linkedin: "LinkedIn",
  trustpilot: "Trustpilot",
  google_business: "Google Business",
  other: "Altra fonte",
};

export function BrandSectionDraftSourcesDrawer({
  open,
  onClose,
  draft,
  facts,
  externalSources = [],
}: BrandSectionDraftSourcesDrawerProps) {
  if (!open) return null;

  const sourceIds = new Set(draft.sourceFactIds ?? []);
  const usedFacts = facts.filter((f) => sourceIds.has(f.id));
  const documentCount = new Set(
    usedFacts.map((f) => f.sourceDocumentId).filter((id): id is string => Boolean(id))
  ).size;

  const extIds = new Set(draft.sourceExternalIds ?? []);
  const usedExternal = externalSources.filter((s) => extIds.has(s.id));

  return (
    <div className="bi-sources-drawer">
      <div className="bi-sources-drawer__backdrop" onClick={onClose} role="presentation" />
      <div className="bi-sources-drawer__panel">
        <div className="bi-sources-drawer__header">
          <h4>Fonti — {draft.title}</h4>
          <button type="button" className="gcr-btn gcr-btn--ghost gcr-btn--sm" onClick={onClose}>
            Chiudi
          </button>
        </div>
        <p className="bi-panel__subtitle">
          {usedFacts.length} facts file · {documentCount} documenti
          {usedExternal.length > 0 && ` · ${usedExternal.length} fonti esterne`}
        </p>

        {usedExternal.length > 0 && (
          <div className="bi-sources-drawer__external">
            <h5>Fonti web / social / recensioni</h5>
            <ul className="bi-analyzed-sources__list">
              {usedExternal.map((source) => (
                <li key={source.id} className="bi-analyzed-source">
                  <span className="bi-analyzed-source__type">
                    {TYPE_LABELS[source.sourceType] ?? source.sourceType}
                  </span>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="bi-analyzed-source__url"
                  >
                    {source.url}
                  </a>
                  {source.fetchedSummary && (
                    <p className="bi-analyzed-source__summary">{source.fetchedSummary}</p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        <BrandExtractedFactsReview
          facts={usedFacts}
          onApprove={() => {}}
          onReject={() => {}}
          onMoveSection={() => {}}
          onEditValue={() => {}}
          onApply={() => {}}
        />
      </div>
    </div>
  );
}
