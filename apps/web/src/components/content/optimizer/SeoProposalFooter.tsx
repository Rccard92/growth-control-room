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
  applyDisabled?: boolean;
  saveDisabled?: boolean;
  onApplySelected: () => void;
  onSaveDraft: () => void;
  onCancel: () => void;
}

export function SeoProposalFooter({
  writeProductsAvailable,
  openaiConfigured,
  loading,
  saveLoading,
  applyLoading,
  applyDisabled,
  saveDisabled,
  onApplySelected,
  onSaveDraft,
  onCancel,
}: SeoProposalFooterProps) {
  return (
    <div className="seo-proposal-footer">
      {!openaiConfigured && (
        <p className="seo-proposal-footer__hint">{AI_DISABLED_MSG}</p>
      )}
      <div className="seo-proposal-footer__actions">
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
        <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onCancel}>
          Annulla
        </button>
      </div>
    </div>
  );
}
