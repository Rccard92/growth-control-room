import type { SeoEntityAnalysis, SeoOptimizationProposal } from "@gcr/shared";
import { SeoScoreBadge } from "./SeoScoreBadge";

interface SeoDetailDrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  analysis: SeoEntityAnalysis | undefined;
  proposal: SeoOptimizationProposal | undefined;
  writeProductsAvailable: boolean;
  onApprove: () => void;
  onApply: () => void;
  onReject: () => void;
  actionLoading?: boolean;
}

function JsonBlock({ data }: { data: unknown }) {
  return (
    <pre className="seo-drawer__json">{JSON.stringify(data, null, 2)}</pre>
  );
}

export function SeoDetailDrawer({
  open,
  onClose,
  title,
  analysis,
  proposal,
  writeProductsAvailable,
  onApprove,
  onApply,
  onReject,
  actionLoading,
}: SeoDetailDrawerProps) {
  if (!open) return null;

  return (
    <div className="seo-drawer-backdrop" onClick={onClose} role="presentation">
      <aside
        className="seo-drawer gcr-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Dettaglio SEO"
      >
        <header className="seo-drawer__header">
          <div>
            <p className="gcr-card__label">Dettaglio SEO</p>
            <h3>{title}</h3>
          </div>
          <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
            Chiudi
          </button>
        </header>

        {analysis && (
          <section className="seo-drawer__section">
            <h4>Score breakdown</h4>
            <div className="seo-drawer__scores">
              <div>
                Totale <SeoScoreBadge score={analysis.scoreTotal} severity={analysis.severity} />
              </div>
              <div>Title: {analysis.scoreTitle}</div>
              <div>SEO title: {analysis.scoreSeoTitle}</div>
              <div>Meta desc: {analysis.scoreMetaDescription}</div>
              <div>Description: {analysis.scoreDescription}</div>
              <div>Alt immagini: {analysis.scoreImageAlt}</div>
              <div>Handle: {analysis.scoreHandle}</div>
            </div>
            {analysis.issues && analysis.issues.length > 0 && (
              <>
                <h4>Issues</h4>
                <JsonBlock data={analysis.issues} />
              </>
            )}
          </section>
        )}

        {proposal && (
          <section className="seo-drawer__section">
            <h4>Proposta ({proposal.status})</h4>
            <p className="seo-drawer__risk">Risk: {proposal.riskLevel} · Source: {proposal.source}</p>
            <h5>Valori attuali</h5>
            <JsonBlock data={proposal.currentValues} />
            <h5>Valori proposti</h5>
            <JsonBlock data={proposal.proposedValues} />
            {proposal.reasoning && (
              <>
                <h5>Reasoning</h5>
                <JsonBlock data={proposal.reasoning} />
              </>
            )}
            <div className="seo-drawer__actions">
              {proposal.status === "draft" && (
                <>
                  <button
                    type="button"
                    className="gcr-btn gcr-btn--primary"
                    disabled={actionLoading}
                    onClick={onApprove}
                  >
                    Approva
                  </button>
                  <button
                    type="button"
                    className="gcr-btn gcr-btn--secondary"
                    disabled={actionLoading}
                    onClick={onReject}
                  >
                    Rifiuta
                  </button>
                </>
              )}
              {proposal.status === "approved" && (
                <button
                  type="button"
                  className="gcr-btn gcr-btn--primary"
                  disabled={actionLoading || !writeProductsAvailable}
                  title={
                    writeProductsAvailable
                      ? undefined
                      : "Per applicare le modifiche su Shopify serve autorizzare write_products."
                  }
                  onClick={onApply}
                >
                  Applica su Shopify
                </button>
              )}
            </div>
          </section>
        )}
      </aside>
    </div>
  );
}
