import type { SeoOptimizationProposal } from "@gcr/shared";

const AI_DISABLED_MSG =
  "AI non configurata. Puoi modificare manualmente e salvare come proposta.";

const WRITE_PRODUCTS_MSG =
  "Per applicare su Shopify serve autorizzare write_products.";

interface SeoProposalFooterProps {
  proposal: SeoOptimizationProposal | null | undefined;
  writeProductsAvailable: boolean;
  openaiConfigured: boolean;
  loading?: boolean;
  saveLoading?: boolean;
  generateLoading?: boolean;
  onSaveDraft: () => void;
  onGenerateAi: () => void;
  onApprove: () => void;
  onReject: () => void;
  onApply: () => void;
  onCancel: () => void;
}

export function SeoProposalFooter({
  proposal,
  writeProductsAvailable,
  openaiConfigured,
  loading,
  saveLoading,
  generateLoading,
  onSaveDraft,
  onGenerateAi,
  onApprove,
  onReject,
  onApply,
  onCancel,
}: SeoProposalFooterProps) {
  const canApprove = proposal?.status === "draft" || proposal?.status === "rejected";
  const canApply = proposal?.status === "approved";

  return (
    <div className="seo-proposal-footer">
      {!openaiConfigured && (
        <p className="seo-proposal-footer__hint">{AI_DISABLED_MSG}</p>
      )}
      {!writeProductsAvailable && (
        <p className="seo-proposal-footer__hint">{WRITE_PRODUCTS_MSG}</p>
      )}
      {proposal && (
        <p className="seo-proposal-footer__status">
          Proposta {proposal.id.slice(0, 8)}… · {proposal.status} · {proposal.source}
        </p>
      )}
      <div className="seo-proposal-footer__actions">
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary"
          disabled={saveLoading || loading}
          onClick={onSaveDraft}
        >
          {saveLoading ? "Salvataggio…" : "Salva come proposta"}
        </button>
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          disabled={!openaiConfigured || generateLoading || loading}
          title={openaiConfigured ? undefined : AI_DISABLED_MSG}
          onClick={onGenerateAi}
        >
          {generateLoading ? "Generazione…" : "Genera proposta AI"}
        </button>
        {proposal && canApprove && (
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
        {proposal && canApply && (
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={loading || !writeProductsAvailable}
            title={
              writeProductsAvailable
                ? undefined
                : WRITE_PRODUCTS_MSG
            }
            onClick={onApply}
          >
            Applica su Shopify
          </button>
        )}
        <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onCancel}>
          Annulla
        </button>
      </div>
    </div>
  );
}
