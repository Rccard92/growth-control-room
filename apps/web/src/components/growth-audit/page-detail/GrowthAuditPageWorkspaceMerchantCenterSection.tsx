import { useState } from "react";
import type { GrowthAuditMerchantCenterIssue, GrowthAuditPage } from "@gcr/shared";
import {
  getGrowthAuditPageMerchantCenterMetadata,
  getGrowthAuditMerchantCenterStatusBadgeClass,
  getGrowthAuditMerchantCenterStatusLabel,
  hasGrowthAuditPageMerchantCenterData,
  isGrowthAuditProductPage,
} from "../../../lib/growth-audit-utils";

interface GrowthAuditPageWorkspaceMerchantCenterSectionProps {
  page: GrowthAuditPage;
}

function formatMoney(value?: number | null, currency?: string | null): string {
  if (value == null) return "—";
  const formatted = value.toLocaleString("it-IT", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return currency ? `${formatted} ${currency}` : formatted;
}

export function GrowthAuditPageWorkspaceMerchantCenterSection({
  page,
}: GrowthAuditPageWorkspaceMerchantCenterSectionProps) {
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  if (!isGrowthAuditProductPage(page)) {
    return null;
  }

  const merchantMeta = getGrowthAuditPageMerchantCenterMetadata(page);
  const hasData = hasGrowthAuditPageMerchantCenterData(page);
  const issues = ((merchantMeta?.issues ?? []) as GrowthAuditMerchantCenterIssue[]).slice(0, 5);
  const isNoMatch = merchantMeta?.matchStatus === "no_reliable_match" || merchantMeta?.matchedBy === "none";

  return (
    <section
      id="merchant-center"
      className="growth-audit-merchant-center growth-audit-workspace-section gcr-card"
    >
      <header className="growth-audit-workspace-section__header">
        <h2 className="growth-audit-workspace-section__title">Merchant Center</h2>
        <p className="growth-audit-workspace-section__subtitle">
          Stato feed Shopping e issue diagnostiche per questo prodotto.
        </p>
      </header>

      {!hasData ? (
        <p className="growth-audit-merchant-center__empty">
          Nessun dato Merchant Center sincronizzato per questa pagina nella run attuale.
        </p>
      ) : isNoMatch ? (
        <p className="growth-audit-merchant-center__empty">
          Nessun match affidabile tra feed Merchant Center e questa pagina prodotto.
        </p>
      ) : (
        <>
          <div className="growth-audit-merchant-center__grid">
            <div className="growth-audit-merchant-center__metric">
              <span className="growth-audit-merchant-center__metric-label">Status feed</span>
              <strong
                className={`growth-audit-merchant-center__status-badge ${getGrowthAuditMerchantCenterStatusBadgeClass(merchantMeta?.status)}`}
              >
                {getGrowthAuditMerchantCenterStatusLabel(merchantMeta?.status)}
              </strong>
            </div>
            <div className="growth-audit-merchant-center__metric">
              <span className="growth-audit-merchant-center__metric-label">Disponibilità</span>
              <strong className="growth-audit-merchant-center__metric-value">
                {merchantMeta?.availability ?? "—"}
              </strong>
            </div>
            <div className="growth-audit-merchant-center__metric">
              <span className="growth-audit-merchant-center__metric-label">Prezzo feed</span>
              <strong className="growth-audit-merchant-center__metric-value">
                {formatMoney(merchantMeta?.price, merchantMeta?.currency)}
              </strong>
            </div>
            <div className="growth-audit-merchant-center__metric">
              <span className="growth-audit-merchant-center__metric-label">Issue</span>
              <strong className="growth-audit-merchant-center__metric-value">
                {merchantMeta?.issuesCount ?? 0}
                {(merchantMeta?.criticalIssuesCount ?? 0) > 0
                  ? ` (${merchantMeta?.criticalIssuesCount} critiche)`
                  : ""}
              </strong>
            </div>
          </div>

          {issues.length > 0 && (
            <div className="growth-audit-merchant-center__issues">
              <h3 className="growth-audit-merchant-center__issues-title">Issue principali</h3>
              <ul className="growth-audit-merchant-center__issues-list">
                {issues.map((issue, index) => (
                  <li key={`${issue.code ?? "issue"}-${index}`}>
                    <span className="growth-audit-merchant-center__issue-code">
                      {issue.code ?? "issue"}
                    </span>
                    {issue.severity && (
                      <span className="growth-audit-merchant-center__issue-severity">
                        {issue.severity}
                      </span>
                    )}
                    <p>{issue.description ?? issue.detail ?? "Issue senza descrizione."}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <details
            className="growth-audit-merchant-center__technical"
            open={showTechnicalDetails}
            onToggle={(event) => setShowTechnicalDetails(event.currentTarget.open)}
          >
            <summary>Dettagli tecnici matching</summary>
            <dl className="growth-audit-merchant-center__technical-grid">
              <div>
                <dt>Matched by</dt>
                <dd>{merchantMeta?.matchedBy ?? "—"}</dd>
              </div>
              <div>
                <dt>Offer ID</dt>
                <dd>{merchantMeta?.offerId ?? "—"}</dd>
              </div>
              <div>
                <dt>GTIN</dt>
                <dd>{merchantMeta?.gtin ?? "—"}</dd>
              </div>
              <div>
                <dt>MPN</dt>
                <dd>{merchantMeta?.mpn ?? "—"}</dd>
              </div>
              <div>
                <dt>Brand</dt>
                <dd>{merchantMeta?.brand ?? "—"}</dd>
              </div>
              <div>
                <dt>Ultimo sync</dt>
                <dd>
                  {merchantMeta?.syncedAt
                    ? new Date(merchantMeta.syncedAt).toLocaleString("it-IT")
                    : "—"}
                </dd>
              </div>
            </dl>
            {merchantMeta?.matchDebug && (
              <pre className="growth-audit-merchant-center__debug">
                {JSON.stringify(merchantMeta.matchDebug, null, 2)}
              </pre>
            )}
          </details>
        </>
      )}
    </section>
  );
}
