import type { SeoProposalPreviewResponse } from "@gcr/shared";

interface SeoProposalPreviewProps {
  preview: SeoProposalPreviewResponse | undefined;
  loading?: boolean;
}

export function SeoProposalPreview({ preview, loading }: SeoProposalPreviewProps) {
  if (loading) {
    return <div className="gcr-skeleton seo-skeleton-row" />;
  }
  if (!preview) {
    return (
      <p className="shopify-empty-copy">
        Nessuna proposta da mostrare. Salva manualmente o genera una proposta AI.
      </p>
    );
  }

  const changed = preview.fields.filter((f) => f.changed);

  return (
    <div className="seo-proposal-preview">
      <div className="seo-proposal-preview__meta">
        <span>Stato: {preview.status}</span>
        <span>Fonte: {preview.source}</span>
        <span>Rischio: {preview.riskLevel}</span>
      </div>
      {preview.reasoning && preview.reasoning.length > 0 && (
        <div className="seo-proposal-preview__reasoning">
          <strong>Motivazione</strong>
          <ul>
            {preview.reasoning.map((r, i) => (
              <li key={i}>{String(r)}</li>
            ))}
          </ul>
        </div>
      )}
      {changed.length === 0 ? (
        <p className="shopify-empty-copy">Nessuna differenza rispetto ai valori attuali.</p>
      ) : (
        <div className="seo-proposal-preview__diff">
          {changed.map((field) => (
            <div key={field.field} className="seo-proposal-preview__row">
              <strong>{field.field}</strong>
              <div className="seo-proposal-preview__cols">
                <div>
                  <span className="seo-proposal-preview__label">Attuale</span>
                  <pre>{formatValue(field.current)}</pre>
                </div>
                <div>
                  <span className="seo-proposal-preview__label">Proposto</span>
                  <pre>{formatValue(field.proposed)}</pre>
                </div>
              </div>
              {field.reasoning && (
                <p className="seo-proposal-preview__field-reason">{field.reasoning}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function formatValue(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "string") return value || "—";
  return JSON.stringify(value, null, 2);
}
