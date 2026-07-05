import type { GrowthAuditGa4MatchDebug, GrowthAuditPage } from "@gcr/shared";
import {
  getGrowthAuditPageGa4EcommerceMetadata,
  isGrowthAuditProductPage,
} from "../../../lib/growth-audit-utils";

interface GrowthAuditPageWorkspaceGa4EcommerceSectionProps {
  page: GrowthAuditPage;
}

function formatNumber(value?: number | null): string {
  if (value == null) return "—";
  return value.toLocaleString("it-IT");
}

function formatMoney(value?: number | null, currency?: string | null): string {
  if (value == null) return "—";
  const formatted = value.toLocaleString("it-IT", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return currency ? `${formatted} ${currency}` : formatted;
}

function formatRate(value?: number | null): string {
  if (value == null) return "—";
  return `${(value * 100).toLocaleString("it-IT", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

function formatMatchTypeLabel(matchedBy?: string | null): string {
  switch (matchedBy) {
    case "item_id":
      return "item_id";
    case "variant_id":
      return "variant_id";
    case "sku":
      return "sku";
    case "item_name":
      return "item_name";
    default:
      return matchedBy ?? "none";
  }
}

function buildFunnelDiagnosis(
  meta: NonNullable<ReturnType<typeof getGrowthAuditPageGa4EcommerceMetadata>>,
): string | null {
  const itemViews = meta.itemViews ?? meta.itemViewEvents ?? 0;
  const itemsAddedToCart = meta.itemsAddedToCart ?? 0;
  const itemsCheckedOut = meta.itemsCheckedOut ?? 0;
  const itemsPurchased = meta.itemsPurchased ?? 0;

  if (meta.matchedBy === "none" || meta.matchDebug?.matchStatus === "no_reliable_match") {
    return null;
  }
  if (itemViews > 50 && itemsAddedToCart === 0) {
    return "Il prodotto viene visto ma non entra nel carrello. Problema probabile: offerta, prezzo, trust, immagini o CTA.";
  }
  if (itemsAddedToCart > 0 && itemsCheckedOut === 0) {
    return "Gli utenti aggiungono al carrello ma non iniziano il checkout. Verifica costi, spedizione, carrello e fiducia.";
  }
  if (itemsCheckedOut > 0 && itemsPurchased === 0) {
    return "Gli utenti arrivano al checkout ma non acquistano. Verifica checkout, pagamento, spedizione e costi finali.";
  }
  if (itemsPurchased > 0) {
    return "Il prodotto genera acquisti. Migliorare la pagina può amplificare una domanda già validata.";
  }
  return null;
}

function hasGa4EcommerceZeroData(
  meta: NonNullable<ReturnType<typeof getGrowthAuditPageGa4EcommerceMetadata>>,
): boolean {
  if (!meta.syncedAt) return false;
  if (meta.matchDebug?.matchStatus === "no_reliable_match") return false;
  const itemViews = meta.itemViews ?? meta.itemViewEvents ?? 0;
  return (
    itemViews === 0 &&
    (meta.itemsAddedToCart ?? 0) === 0 &&
    (meta.itemsCheckedOut ?? 0) === 0 &&
    (meta.itemsPurchased ?? 0) === 0 &&
    (meta.itemRevenue ?? 0) === 0
  );
}

function renderMatchDebugBlock(matchDebug: GrowthAuditGa4MatchDebug) {
  const keys = matchDebug.shopifyKeys;
  const isNoMatch = matchDebug.matchStatus === "no_reliable_match";

  return (
    <div className="growth-audit-ga4-funnel__match-debug">
      {isNoMatch ? (
        <>
          <h3 className="growth-audit-ga4-funnel__match-debug-title">
            Dati GA4 non abbinati a questo prodotto
          </h3>
          <p className="growth-audit-ga4-funnel__match-debug-copy">
            Il funnel aggregato GA4 contiene dati item-level, ma questo prodotto non è stato
            collegato in modo affidabile. Per evitare dati falsati, il tool non assegna metriche
            finché item_id, variant_id, SKU o nome prodotto non coincidono.
          </p>
        </>
      ) : (
        <p className="growth-audit-ga4-funnel__match-debug-copy">
          Match affidabile tramite:{" "}
          <strong>{formatMatchTypeLabel(matchDebug.matchedBy)}</strong>
        </p>
      )}

      <div className="growth-audit-ga4-funnel__match-debug-keys">
        <div>
          <span>Product legacy id</span>
          <strong>{keys.productLegacyId ?? "—"}</strong>
        </div>
        <div>
          <span>Variant ids</span>
          <strong>
            {keys.variantLegacyIds && keys.variantLegacyIds.length > 0
              ? keys.variantLegacyIds.join(", ")
              : "—"}
          </strong>
        </div>
        <div>
          <span>SKU</span>
          <strong>
            {keys.skus && keys.skus.length > 0 ? keys.skus.join(", ") : "—"}
          </strong>
        </div>
        <div>
          <span>Title normalizzato</span>
          <strong>{keys.titleNormalized || "—"}</strong>
        </div>
        <div>
          <span>Handle</span>
          <strong>{keys.handleNormalized || "—"}</strong>
        </div>
        <div>
          <span>Match status</span>
          <strong>{matchDebug.matchStatus}</strong>
        </div>
        <div>
          <span>Matched by</span>
          <strong>{matchDebug.matchedBy ?? "none"}</strong>
        </div>
      </div>

      <p className="growth-audit-ga4-funnel__match-debug-reason">{matchDebug.reason}</p>

      {matchDebug.candidateItems.length > 0 && (
        <div className="growth-audit-ga4-funnel__match-debug-candidates">
          <h4>Possibili item GA4 da verificare manualmente</h4>
          <p className="growth-audit-ga4-funnel__match-debug-note">
            Questi dati non sono stati assegnati al prodotto.
          </p>
          <table className="growth-audit-ga4-funnel__match-debug-candidates-table">
            <thead>
              <tr>
                <th>itemId</th>
                <th>itemName</th>
                <th>Variant</th>
                <th>Views</th>
                <th>Cart</th>
                <th>Purchase</th>
                <th>Revenue</th>
                <th>Motivo</th>
              </tr>
            </thead>
            <tbody>
              {matchDebug.candidateItems.map((candidate, index) => (
                <tr key={`${candidate.itemId}-${candidate.itemName}-${index}`}>
                  <td>{candidate.itemId || "—"}</td>
                  <td>{candidate.itemName || "—"}</td>
                  <td>{candidate.itemVariant || "—"}</td>
                  <td>{formatNumber(candidate.itemsViewed)}</td>
                  <td>{formatNumber(candidate.itemsAddedToCart)}</td>
                  <td>{formatNumber(candidate.itemsPurchased)}</td>
                  <td>{formatMoney(candidate.itemRevenue)}</td>
                  <td>{candidate.candidateReason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function GrowthAuditPageWorkspaceGa4EcommerceSection({
  page,
}: GrowthAuditPageWorkspaceGa4EcommerceSectionProps) {
  if (!isGrowthAuditProductPage(page)) {
    return null;
  }

  const funnelMeta = getGrowthAuditPageGa4EcommerceMetadata(page);
  const diagnosis = funnelMeta ? buildFunnelDiagnosis(funnelMeta) : null;
  const isZeroData = funnelMeta ? hasGa4EcommerceZeroData(funnelMeta) : false;
  const isNoReliableMatch = funnelMeta?.matchDebug?.matchStatus === "no_reliable_match";
  const isMatched = funnelMeta?.matchDebug?.matchStatus === "matched";

  const funnelSteps = funnelMeta
    ? [
        {
          label: "View item",
          value: formatNumber(funnelMeta.itemViews ?? funnelMeta.itemViewEvents),
        },
        {
          label: "Add to cart",
          value: formatNumber(funnelMeta.itemsAddedToCart),
        },
        {
          label: "Begin checkout",
          value: formatNumber(funnelMeta.itemsCheckedOut),
        },
        {
          label: "Purchase",
          value: formatNumber(funnelMeta.itemsPurchased),
        },
      ]
    : [];

  return (
    <section
      id="ga4-ecommerce-funnel"
      className="growth-audit-ga4-funnel growth-audit-workspace-section gcr-card"
    >
      <header className="growth-audit-workspace-section__header">
        <h2 className="growth-audit-workspace-section__title">GA4 Ecommerce Funnel</h2>
        <p className="growth-audit-workspace-section__subtitle">
          Mostra il percorso ecommerce item-level del prodotto: visualizzazione, carrello,
          checkout e acquisto.
        </p>
      </header>

      {funnelMeta ? (
        <>
          {funnelMeta.matchDebug && renderMatchDebugBlock(funnelMeta.matchDebug)}

          {!isNoReliableMatch && (
            <>
              <div className="growth-audit-ga4-funnel__steps">
                {funnelSteps.map((step, index) => (
                  <div key={step.label} className="growth-audit-ga4-funnel__step-wrap">
                    {index > 0 && <span className="growth-audit-ga4-funnel__arrow">→</span>}
                    <div className="growth-audit-ga4-funnel__step">
                      <span className="growth-audit-ga4-funnel__step-label">{step.label}</span>
                      <strong className="growth-audit-ga4-funnel__step-value">{step.value}</strong>
                    </div>
                  </div>
                ))}
              </div>

              <div className="growth-audit-ga4-funnel__rates">
                <div>
                  <span>Item revenue</span>
                  <strong>{formatMoney(funnelMeta.itemRevenue, funnelMeta.currency)}</strong>
                </div>
                <div>
                  <span>View → cart</span>
                  <strong>{formatRate(funnelMeta.viewToCartRate)}</strong>
                </div>
                <div>
                  <span>Cart → checkout</span>
                  <strong>{formatRate(funnelMeta.cartToCheckoutRate)}</strong>
                </div>
                <div>
                  <span>Checkout → purchase</span>
                  <strong>{formatRate(funnelMeta.checkoutToPurchaseRate)}</strong>
                </div>
                <div>
                  <span>View → purchase</span>
                  <strong>{formatRate(funnelMeta.viewToPurchaseRate)}</strong>
                </div>
                <div>
                  <span>Cart → purchase</span>
                  <strong>{formatRate(funnelMeta.cartToPurchaseRate)}</strong>
                </div>
              </div>
            </>
          )}

          {isMatched && (
            <p className="growth-audit-ga4-funnel__match">
              Match affidabile tramite:{" "}
              <strong>{formatMatchTypeLabel(funnelMeta.matchedBy)}</strong>
              {funnelMeta.matchedItemIds && funnelMeta.matchedItemIds.length > 0
                ? ` · ID: ${funnelMeta.matchedItemIds.join(", ")}`
                : ""}
            </p>
          )}

          {diagnosis && (
            <p className="growth-audit-ga4-funnel__diagnosis">{diagnosis}</p>
          )}

          {isZeroData && (
            <p className="growth-audit-ga4-funnel__empty">
              Nessun dato ecommerce item-level trovato per questo periodo. Prova 90 giorni o verifica
              in GA4 DebugView/Reports se gli eventi view_item, add_to_cart e purchase sono
              presenti.
            </p>
          )}
        </>
      ) : (
        <p className="growth-audit-ga4-funnel__empty">
          Questa pagina non ha ancora dati funnel ecommerce GA4 nella run attuale.
        </p>
      )}
    </section>
  );
}
