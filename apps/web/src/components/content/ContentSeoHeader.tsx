interface ContentSeoHeaderProps {
  onSync: () => void;
  onAnalyze: () => void;
  syncLoading: boolean;
  analyzeLoading: boolean;
  shopifyConnected: boolean;
}

export function ContentSeoHeader({
  onSync,
  onAnalyze,
  syncLoading,
  analyzeLoading,
  shopifyConnected,
}: ContentSeoHeaderProps) {
  return (
    <div className="content-seo-header">
      <div>
        <p className="gcr-card__label">Modulo SEO</p>
        <h2 className="content-seo-header__title">Content SEO Room</h2>
        <p className="content-seo-header__subtitle">
          Audit contenuti Shopify, opportunità editoriali e internal linking
        </p>
      </div>
      <div className="content-seo-header__actions">
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary"
          onClick={onSync}
          disabled={!shopifyConnected || syncLoading}
        >
          {syncLoading ? "Sincronizzazione…" : "Sincronizza contenuti Shopify"}
        </button>
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          onClick={onAnalyze}
          disabled={!shopifyConnected || analyzeLoading}
        >
          {analyzeLoading ? "Analisi…" : "Analizza SEO"}
        </button>
      </div>
    </div>
  );
}
