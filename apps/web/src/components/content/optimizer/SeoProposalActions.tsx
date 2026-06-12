import type { SeoOptimizationProposal } from "@gcr/shared";

interface SeoProposalActionsProps {
  proposal: SeoOptimizationProposal | null | undefined;
  writeProductsAvailable: boolean;
  loading?: boolean;
  onSaveDraft?: () => void;
  onGenerateAi?: () => void;
  aiDisabled?: boolean;
  aiTooltip?: string;
  saveLoading?: boolean;
  generateLoading?: boolean;
  onApprove: () => void;
  onReject: () => void;
  onApply: () => void;
}

export function SeoProposalActions({
  proposal,
  writeProductsAvailable,
  loading,
  onSaveDraft,
  onGenerateAi,
  aiDisabled,
  aiTooltip,
  saveLoading,
  generateLoading,
  onApprove,
  onReject,
  onApply,
}: SeoProposalActionsProps) {
  const canApprove = proposal?.status === "draft" || proposal?.status === "rejected";
  const canApply = proposal?.status === "approved";

  return (
    <div className="seo-proposal-actions">
      <div className="seo-drawer__actions">
        {onSaveDraft && (
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            disabled={saveLoading || loading}
            onClick={onSaveDraft}
          >
            {saveLoading ? "Salvataggio…" : "Salva come proposta"}
          </button>
        )}
        {onGenerateAi && (
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={aiDisabled || generateLoading || loading}
            title={aiTooltip}
            onClick={onGenerateAi}
          >
            {generateLoading ? "Generazione…" : "Genera proposta AI"}
          </button>
        )}
      </div>

      {proposal && (
        <>
          <p className="seo-proposal-actions__status">
            Proposta {proposal.id.slice(0, 8)}… · {proposal.status} · {proposal.source}
          </p>
          <div className="seo-drawer__actions">
            {canApprove && (
              <>
                <button
                  type="button"
                  className="gcr-btn gcr-btn--secondary"
                  disabled={loading}
                  onClick={onReject}
                >
                  Rifiuta
                </button>
                <button
                  type="button"
                  className="gcr-btn gcr-btn--primary"
                  disabled={loading}
                  onClick={onApprove}
                >
                  Approva
                </button>
              </>
            )}
            {canApply && (
              <button
                type="button"
                className="gcr-btn gcr-btn--primary"
                disabled={loading || !writeProductsAvailable}
                title={
                  writeProductsAvailable
                    ? undefined
                    : "Per applicare modifiche su Shopify serve riconnettere l'app con write_products."
                }
                onClick={onApply}
              >
                Applica su Shopify
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
