const AI_DISABLED_MSG =
  "AI non configurata. Puoi modificare manualmente e salvare come bozza.";

const WRITE_PRODUCTS_MSG =
  "Per applicare su Shopify serve autorizzare write_products.";

interface SeoProposalFooterProps {
  writeProductsAvailable: boolean;
  openaiConfigured: boolean;
  loading?: boolean;
  saveLoading?: boolean;
  applyLoading?: boolean;
  generateLoading?: boolean;
  applyDisabled?: boolean;
  saveDisabled?: boolean;
  applyDisabledMessage?: string;
  saveDisabledMessage?: string;
  onApplySelected: () => void;
  onSaveDraft: () => void;
  onGenerateAi: () => void;
  onCancel: () => void;
}

export function SeoProposalFooter({
  writeProductsAvailable,
  openaiConfigured,
  loading,
  saveLoading,
  applyLoading,
  generateLoading,
  applyDisabled,
  saveDisabled,
  applyDisabledMessage,
  saveDisabledMessage,
  onApplySelected,
  onSaveDraft,
  onGenerateAi,
  onCancel,
}: SeoProposalFooterProps) {
  return (
    <div className="seo-proposal-footer">
      {!openaiConfigured && (
        <p className="seo-proposal-footer__hint">{AI_DISABLED_MSG}</p>
      )}
      <div className="seo-proposal-footer__actions">
        {applyDisabled && applyDisabledMessage && (
          <p className="seo-proposal-footer__hint">{applyDisabledMessage}</p>
        )}
        <div className="seo-proposal-footer__apply-group">
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={applyLoading || loading || applyDisabled || !writeProductsAvailable}
            title={writeProductsAvailable ? undefined : WRITE_PRODUCTS_MSG}
            onClick={onApplySelected}
          >
            {applyLoading ? "Applicazione…" : "Applica modifiche selezionate"}
          </button>
          {!writeProductsAvailable && (
            <p className="seo-proposal-footer__hint seo-proposal-footer__hint--inline">
              {WRITE_PRODUCTS_MSG}
            </p>
          )}
        </div>
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary"
          disabled={saveLoading || loading || saveDisabled}
          onClick={onSaveDraft}
        >
          {saveLoading ? "Salvataggio…" : "Salva bozza"}
        </button>
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary"
          disabled={!openaiConfigured || generateLoading || loading}
          title={openaiConfigured ? undefined : AI_DISABLED_MSG}
          onClick={onGenerateAi}
        >
          {generateLoading ? "Generazione…" : "Genera proposta AI"}
        </button>
        <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onCancel}>
          Annulla
        </button>
        {saveDisabled && saveDisabledMessage && (
          <p className="seo-proposal-footer__hint">{saveDisabledMessage}</p>
        )}
      </div>
    </div>
  );
}
