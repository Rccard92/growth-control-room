import type { GrowthAuditAiCoverageStats } from "../../lib/growth-audit-utils";

interface GrowthAuditAiCoveragePanelProps {
  stats: GrowthAuditAiCoverageStats;
}

export function GrowthAuditAiCoveragePanel({ stats }: GrowthAuditAiCoveragePanelProps) {
  return (
    <section className="growth-audit-ai-coverage gcr-card">
      <h3 className="growth-audit-ai-coverage__title">Copertura AI/GEO/CRO</h3>
      <p className="growth-audit-ai-coverage__intro">
        L&apos;analisi AI è manuale e va lanciata pagina per pagina sulle URL prioritarie.
      </p>

      <div className="growth-audit-ai-coverage__stats">
        <div className="growth-audit-ai-coverage__stat">
          <span className="growth-audit-ai-coverage__value">{stats.totalPages}</span>
          <span className="growth-audit-ai-coverage__label">Pagine totali</span>
        </div>
        <div className="growth-audit-ai-coverage__stat">
          <span className="growth-audit-ai-coverage__value">{stats.aiAnalyzedPages}</span>
          <span className="growth-audit-ai-coverage__label">Analizzate con AI</span>
        </div>
        <div className="growth-audit-ai-coverage__stat">
          <span className="growth-audit-ai-coverage__value">{stats.productsWithoutAi}</span>
          <span className="growth-audit-ai-coverage__label">Prodotti senza AI</span>
        </div>
        <div className="growth-audit-ai-coverage__stat">
          <span className="growth-audit-ai-coverage__value">{stats.collectionsWithoutAi}</span>
          <span className="growth-audit-ai-coverage__label">Collection senza AI</span>
        </div>
        <div className="growth-audit-ai-coverage__stat">
          <span className="growth-audit-ai-coverage__value">{stats.strategicWithoutAi}</span>
          <span className="growth-audit-ai-coverage__label">Strategiche senza AI</span>
        </div>
      </div>

      <div className="growth-audit-coverage-bar" aria-label="Copertura AI">
        <div
          className="growth-audit-coverage-bar__fill"
          style={{ width: `${Math.min(100, stats.coveragePercent)}%` }}
        />
        <span className="growth-audit-coverage-bar__label">{stats.coveragePercent}% copertura</span>
      </div>

      <p className="growth-audit-ai-coverage__cta-note">
        Apri le pagine prioritarie e lancia AI/GEO/CRO manualmente.
      </p>
    </section>
  );
}
