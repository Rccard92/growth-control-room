import type { BrandExtractedFact, BrandSectionDraftListItem } from "@gcr/shared";
import { BrandExtractedFactsReview } from "./BrandExtractedFactsReview";

interface BrandSectionDraftSourcesDrawerProps {
  open: boolean;
  onClose: () => void;
  draft: BrandSectionDraftListItem;
  facts: BrandExtractedFact[];
}

export function BrandSectionDraftSourcesDrawer({
  open,
  onClose,
  draft,
  facts,
}: BrandSectionDraftSourcesDrawerProps) {
  if (!open) return null;

  const sourceIds = new Set(draft.sourceFactIds ?? []);
  const usedFacts = facts.filter((f) => sourceIds.has(f.id));
  const documentCount = new Set(
    usedFacts.map((f) => f.sourceDocumentId).filter((id): id is string => Boolean(id))
  ).size;

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
          {usedFacts.length} facts usati · {documentCount} documenti
        </p>
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
