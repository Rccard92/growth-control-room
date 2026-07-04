import type { GrowthAuditPage, GrowthAuditPageAiMetadata } from "@gcr/shared";
import {
  getGrowthAuditPageInventoryStatusLabel,
  getGrowthAuditPageSourceLabel,
  getGrowthAuditSourceBadgeClass,
  getGrowthAuditSourceEntityTypeLabel,
  isGrowthAuditPageShopifyLinked,
  mapGrowthAuditPageToSeoEntity,
} from "../../../lib/growth-audit-utils";

interface GrowthAuditPageDetailSidebarProps {
  page: GrowthAuditPage;
  onScrollToSection: (sectionId: string) => void;
  shopifySectionAvailable: boolean;
  aiSectionAvailable: boolean;
}

function readAiMetadata(page: GrowthAuditPage): GrowthAuditPageAiMetadata | null {
  const ai = page.metadata?.ai;
  if (!ai || typeof ai !== "object") return null;
  return ai as GrowthAuditPageAiMetadata;
}

function formatDate(value?: string | null): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("it-IT");
  } catch {
    return value;
  }
}

export function GrowthAuditPageDetailSidebar({
  page,
  onScrollToSection,
  shopifySectionAvailable,
  aiSectionAvailable,
}: GrowthAuditPageDetailSidebarProps) {
  const aiMeta = readAiMetadata(page);
  const shopifyLinked = isGrowthAuditPageShopifyLinked(page);
  const mappedEntity = mapGrowthAuditPageToSeoEntity(page);

  return (
    <aside className="growth-audit-page-detail__sidebar growth-audit-page-detail__sticky-sidebar">
      <section className="growth-audit-page-detail__sidebar-block gcr-card">
        <h3 className="growth-audit-page-detail__sidebar-title">Stato pagina</h3>
        <dl className="growth-audit-page-detail__meta-list">
          <div>
            <dt>Stato</dt>
            <dd>{getGrowthAuditPageInventoryStatusLabel(page.status)}</dd>
          </div>
          <div>
            <dt>Fonte</dt>
            <dd>
              <span className={getGrowthAuditSourceBadgeClass(page.source)}>
                {getGrowthAuditPageSourceLabel(page.source)}
              </span>
            </dd>
          </div>
          <div>
            <dt>HTTP</dt>
            <dd>{page.httpStatus ?? "—"}</dd>
          </div>
          <div>
            <dt>Ultima scansione</dt>
            <dd>{formatDate(page.analyzedAt)}</dd>
          </div>
          <div>
            <dt>Ultima analisi AI</dt>
            <dd>{formatDate(aiMeta?.analyzedAt)}</dd>
          </div>
        </dl>
      </section>

      <section className="growth-audit-page-detail__sidebar-block gcr-card">
        <h3 className="growth-audit-page-detail__sidebar-title">Entità Shopify</h3>
        {shopifyLinked ? (
          <dl className="growth-audit-page-detail__meta-list">
            <div>
              <dt>Tipo</dt>
              <dd>{getGrowthAuditSourceEntityTypeLabel(page.sourceEntityType)}</dd>
            </div>
            {page.sourceEntityTitle && (
              <div>
                <dt>Titolo</dt>
                <dd>{page.sourceEntityTitle}</dd>
              </div>
            )}
            {page.sourceEntityHandle && (
              <div>
                <dt>Handle</dt>
                <dd>{page.sourceEntityHandle}</dd>
              </div>
            )}
          </dl>
        ) : (
          <p className="growth-audit-page-detail__sidebar-note">Nessuna entità collegata</p>
        )}
      </section>

      <section className="growth-audit-page-detail__sidebar-block gcr-card">
        <h3 className="growth-audit-page-detail__sidebar-title">Azioni rapide</h3>
        <div className="growth-audit-page-detail__quick-actions">
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => onScrollToSection("section-priority")}
          >
            Cosa sistemare prima
          </button>
          {shopifySectionAvailable && mappedEntity && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              onClick={() => onScrollToSection("section-shopify")}
            >
              Modifica Shopify
            </button>
          )}
          {aiSectionAvailable && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              onClick={() => onScrollToSection("section-ai")}
            >
              AI/GEO/CRO
            </button>
          )}
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={() => onScrollToSection("section-technical")}
          >
            Dati tecnici
          </button>
        </div>
      </section>

      <section className="growth-audit-page-detail__sidebar-block gcr-card">
        <h3 className="growth-audit-page-detail__sidebar-title">Note operative</h3>
        <p className="growth-audit-page-detail__sidebar-note">
          Correggi title, meta, schema e contenuti. Dopo modifiche Shopify o on-page, riscansiona
          la pagina per aggiornare score e problemi tecnici.
        </p>
      </section>
    </aside>
  );
}
