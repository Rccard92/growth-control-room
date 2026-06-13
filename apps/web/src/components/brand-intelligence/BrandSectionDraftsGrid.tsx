import { useState } from "react";
import type { BrandExternalSource, BrandSectionDraftListItem } from "@gcr/shared";
import { targetSectionLabel } from "./brandImportUtils";
import { BrandSectionDraftEditor } from "./BrandSectionDraftEditor";
import { BrandSectionDraftSourcesDrawer } from "./BrandSectionDraftSourcesDrawer";
import {
  useApplySectionDraft,
  useBrandExtractedFacts,
  usePatchSectionDraft,
  useRegenerateSectionDraft,
  useSectionDraft,
} from "../../hooks/useBrandIntelligence";

interface BrandSectionDraftsGridProps {
  projectId: string;
  batchId: string | null;
  drafts: BrandSectionDraftListItem[];
  externalSources?: BrandExternalSource[];
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: "Bozza",
    needs_review: "Da revisionare",
    approved: "Approvata",
    rejected: "Rifiutata",
    applied: "Applicata",
  };
  return map[status] ?? status;
}

export function BrandSectionDraftsGrid({
  projectId,
  batchId,
  drafts,
  externalSources = [],
}: BrandSectionDraftsGridProps) {
  const [openDraftId, setOpenDraftId] = useState<string | null>(null);
  const [sourcesDraftId, setSourcesDraftId] = useState<string | null>(null);
  const [regenInstructions, setRegenInstructions] = useState("");

  const { data: openDraft } = useSectionDraft(projectId, openDraftId ?? undefined);
  const { data: facts = [] } = useBrandExtractedFacts(projectId, batchId ? { batchId } : undefined);
  const patchDraft = usePatchSectionDraft(projectId);
  const applyDraft = useApplySectionDraft(projectId);
  const regenerate = useRegenerateSectionDraft(projectId);

  const sourcesDraft = drafts.find((d) => d.id === sourcesDraftId);

  if (drafts.length === 0) {
    return (
      <div className="bi-section-drafts-empty gcr-card">
        <p className="bi-panel__subtitle">
          Nessuna bozza sezione ancora. La sintesi parte automaticamente dopo l&apos;estrazione, oppure
          avvia manualmente se OpenAI è configurata.
        </p>
      </div>
    );
  }

  return (
    <div className="bi-section-drafts">
      <div className="bi-section-drafts__grid">
        {drafts.map((draft) => {
          const w = draft.warnings as { messages?: string[] } | null;
          const warnCount = w?.messages?.length ?? 0;
          return (
            <div key={draft.id} className={`bi-section-draft-card bi-section-draft-card--${draft.status}`}>
              <h4 className="bi-section-draft-card__title">
                {draft.title || targetSectionLabel(draft.sectionKey)}
              </h4>
              <span className="bi-section-draft-card__status">{statusLabel(draft.status)}</span>
              {draft.confidence != null && (
                <span className="bi-section-draft-card__confidence">
                  {Math.round(draft.confidence * 100)}% confidence
                </span>
              )}
              {draft.summary && <p className="bi-section-draft-card__summary">{draft.summary}</p>}
              <p className="bi-section-draft-card__meta">
                {(draft.sourceFactIds ?? []).length} facts file
                {(draft.sourceExternalIds ?? []).length > 0 &&
                  ` · ${(draft.sourceExternalIds ?? []).length} fonti esterne`}
                {warnCount > 0 && ` · ${warnCount} warning`}
              </p>
              <div className="bi-section-draft-card__actions">
                <button
                  type="button"
                  className="gcr-btn gcr-btn--primary gcr-btn--sm"
                  onClick={() => setOpenDraftId(draft.id)}
                >
                  Apri bozza
                </button>
                <button
                  type="button"
                  className="gcr-btn gcr-btn--ghost gcr-btn--sm"
                  onClick={() =>
                    patchDraft.mutate({ draftId: draft.id, data: { status: "approved" } })
                  }
                >
                  Approva
                </button>
                <button
                  type="button"
                  className="gcr-btn gcr-btn--ghost gcr-btn--sm"
                  onClick={() =>
                    patchDraft.mutate({ draftId: draft.id, data: { status: "rejected" } })
                  }
                >
                  Rifiuta
                </button>
                <button
                  type="button"
                  className="gcr-btn gcr-btn--ghost gcr-btn--sm"
                  onClick={() => setSourcesDraftId(draft.id)}
                >
                  Vedi fonti
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {openDraftId && openDraft && (
        <div className="bi-section-draft-modal gcr-card">
          <div className="bi-section-draft-modal__header">
            <h3>{openDraft.title}</h3>
            <button type="button" className="gcr-btn gcr-btn--ghost" onClick={() => setOpenDraftId(null)}>
              Chiudi
            </button>
          </div>
          <BrandSectionDraftEditor
            draft={openDraft}
            saving={patchDraft.isPending}
            onSave={(payload) =>
              patchDraft.mutate({ draftId: openDraft.id, data: { draftPayload: payload } })
            }
          />
          <div className="bi-section-draft-modal__actions">
            <input
              type="text"
              placeholder="Istruzioni rigenerazione (opzionale)"
              value={regenInstructions}
              onChange={(e) => setRegenInstructions(e.target.value)}
              className="bi-section-draft-modal__regen-input"
            />
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost gcr-btn--sm"
              disabled={regenerate.isPending}
              onClick={() =>
                regenerate.mutate({
                  draftId: openDraft.id,
                  instructions: regenInstructions || undefined,
                })
              }
            >
              Rigenera sezione
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--primary gcr-btn--sm"
              disabled={applyDraft.isPending}
              onClick={() => {
                patchDraft.mutate(
                  { draftId: openDraft.id, data: { status: "approved" } },
                  {
                    onSuccess: () => applyDraft.mutate(openDraft.id),
                  },
                );
              }}
            >
              Approva e applica
            </button>
          </div>
        </div>
      )}

      {sourcesDraft && (
        <BrandSectionDraftSourcesDrawer
          open={Boolean(sourcesDraftId)}
          onClose={() => setSourcesDraftId(null)}
          draft={sourcesDraft}
          facts={facts}
          externalSources={externalSources}
        />
      )}
    </div>
  );
}
