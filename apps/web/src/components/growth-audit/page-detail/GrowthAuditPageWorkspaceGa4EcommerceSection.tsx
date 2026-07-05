import type {
  GrowthAuditGa4MatchDebug,
  GrowthAuditPage,
  GrowthAuditPageGa4EcommerceVariantMetadata,
} from "@gcr/shared";
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
    case "shopify_composite_item_id":
      return "Shopify composite itemId";
    case "item_id":
      return "item_id";
    case "variant_id":
      return "variant_id";
    case "sku":
      return "sku";
    case "item_name":
      return "item_name";
    case "product_only":
      return "product_only";
    default:
      return matchedBy ?? "none";
  }
}

const SHOPIFY_COMPOSITE_ITEM_ID_RE = /^shopify_[A-Za-z]{2}_\d+_\d+$/i;

function findCompositeGa4ItemId(itemIds?: string[] | null): string | null {
  if (!itemIds?.length) return null;
  return itemIds.find((itemId) => SHOPIFY_COMPOSITE_ITEM_ID_RE.test(itemId)) ?? null;
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

function renderMatchDebugBlock(
  matchDebug: GrowthAuditGa4MatchDebug,
  matchedItemIds?: string[] | null,
) {
  const keys = matchDebug.shopifyKeys;
  const isNoMatch = matchDebug.matchStatus === "no_reliable_match";
  const compositeItemId = findCompositeGa4ItemId(matchedItemIds);

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
        {compositeItemId && (
          <div>
            <span>itemId GA4</span>
            <strong>{compositeItemId}</strong>
          </div>
        )}
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

function sortVariantBreakdown(
  variants: GrowthAuditPageGa4EcommerceVariantMetadata[],
): GrowthAuditPageGa4EcommerceVariantMetadata[] {
  return [...variants].sort((left, right) => {
    const revenueDiff = (right.itemRevenue ?? 0) - (left.itemRevenue ?? 0);
    if (revenueDiff !== 0) return revenueDiff;
    const purchaseDiff = (right.itemsPurchased ?? 0) - (left.itemsPurchased ?? 0);
    if (purchaseDiff !== 0) return purchaseDiff;
    const viewsLeft = left.itemViews ?? left.itemViewEvents ?? 0;
    const viewsRight = right.itemViews ?? right.itemViewEvents ?? 0;
    return viewsRight - viewsLeft;
  });
}

function buildVariantDiagnosisCallouts(
  variants: GrowthAuditPageGa4EcommerceVariantMetadata[],
  bestVariantByRevenue?: string | null,
): string[] {
  const callouts: string[] = [];
  const matchedVariants = variants.filter((variant) => variant.matchedBy && variant.matchedBy !== "none");

  for (const variant of matchedVariants) {
    const views = variant.itemViews ?? variant.itemViewEvents ?? 0;
    const cart = variant.itemsAddedToCart ?? 0;
    const purchases = variant.itemsPurchased ?? 0;
    const title = variant.variantTitle || variant.variantLegacyId || "Variante";

    if (views > 50 && cart === 0) {
      callouts.push(
        `${title}: questa variante viene vista ma convince poco ad entrare nel carrello.`,
      );
    } else if (cart > 5 && purchases === 0) {
      callouts.push(
        `${title}: questa variante entra nel carrello ma perde prima dell'acquisto.`,
      );
    } else if (
      bestVariantByRevenue &&
      variant.variantLegacyId === bestVariantByRevenue &&
      (variant.itemRevenue ?? 0) > 0
    ) {
      callouts.push(
        `${title}: questa variante sta già monetizzando — priorità alta su immagini, stock e copy.`,
      );
    } else if ((variant.stock ?? 1) <= 0 && (views > 0 || cart > 0)) {
      callouts.push(
        `${title}: questa variante ha domanda ma lo stock può limitare vendite.`,
      );
    }

    if (callouts.length >= 3) break;
  }

  return callouts.slice(0, 3);
}

function renderVariantPerformanceSection(
  funnelMeta: NonNullable<ReturnType<typeof getGrowthAuditPageGa4EcommerceMetadata>>,
) {
  const variantBreakdown = funnelMeta.variantBreakdown;
  if (!variantBreakdown || variantBreakdown.length === 0) {
    return (
      <div className="growth-audit-ga4-funnel__variants-empty">
        <h3 className="growth-audit-ga4-funnel__variants-title">Performance varianti</h3>
        <p className="growth-audit-ga4-funnel__variants-subtitle">
          Il prodotto ha funnel aggregato, ma non è ancora disponibile una divisione affidabile per
          variante.
        </p>
      </div>
    );
  }

  const sortedVariants = sortVariantBreakdown(variantBreakdown);
  const callouts = buildVariantDiagnosisCallouts(sortedVariants, funnelMeta.bestVariantByRevenue);

  return (
    <div className="growth-audit-ga4-funnel__variants">
      <header className="growth-audit-ga4-funnel__variants-header">
        <h3 className="growth-audit-ga4-funnel__variants-title">Performance varianti</h3>
        <p className="growth-audit-ga4-funnel__variants-subtitle">
          Le metriche sono divise per variante solo quando GA4 restituisce un itemId/SKU abbinabile in
          modo deterministico.
        </p>
      </header>

      <div className="growth-audit-ga4-funnel__variants-table-wrap">
        <table className="growth-audit-ga4-funnel__variants-table">
          <thead>
            <tr>
              <th>Variante</th>
              <th>SKU</th>
              <th>Stock</th>
              <th>Prezzo</th>
              <th>View item</th>
              <th>Add to cart</th>
              <th>Purchase</th>
              <th>Revenue</th>
              <th>View → cart</th>
              <th>Cart → purchase</th>
              <th>Match</th>
            </tr>
          </thead>
          <tbody>
            {sortedVariants.map((variant) => {
              const isMatched = variant.matchedBy && variant.matchedBy !== "none";
              const isBestRevenue =
                funnelMeta.bestVariantByRevenue &&
                variant.variantLegacyId === funnelMeta.bestVariantByRevenue;
              const views = variant.itemViews ?? variant.itemViewEvents ?? 0;
              const cart = variant.itemsAddedToCart ?? 0;
              const isHighViewLowCart = isMatched && views > 50 && cart === 0;
              const isHighCartLowPurchase =
                isMatched && cart > 5 && (variant.itemsPurchased ?? 0) === 0;
              const isOutOfStockDemand =
                isMatched && (variant.stock ?? 1) <= 0 && (views > 0 || cart > 0);
              const rowClass = [
                isBestRevenue ? "growth-audit-ga4-funnel__variants-row--best-revenue" : "",
                isHighViewLowCart ? "growth-audit-ga4-funnel__variants-row--high-view-low-cart" : "",
                isHighCartLowPurchase
                  ? "growth-audit-ga4-funnel__variants-row--high-cart-low-purchase"
                  : "",
                isOutOfStockDemand ? "growth-audit-ga4-funnel__variants-row--out-of-stock" : "",
              ]
                .filter(Boolean)
                .join(" ");

              return (
                <tr
                  key={variant.variantLegacyId || variant.variantTitle || variant.sku}
                  className={rowClass || undefined}
                >
                  <td>
                    <strong>{variant.variantTitle || "—"}</strong>
                    {!isMatched && (
                      <p className="growth-audit-ga4-funnel__variants-note">
                        Nessun dato item-level abbinato a questa variante nel periodo.
                      </p>
                    )}
                  </td>
                  <td>{variant.sku || "—"}</td>
                  <td>{formatNumber(variant.stock)}</td>
                  <td>{formatMoney(variant.price, funnelMeta.currency)}</td>
                  <td>{formatNumber(views)}</td>
                  <td>{formatNumber(variant.itemsAddedToCart)}</td>
                  <td>{formatNumber(variant.itemsPurchased)}</td>
                  <td>{formatMoney(variant.itemRevenue, funnelMeta.currency)}</td>
                  <td>{formatRate(variant.viewToCartRate)}</td>
                  <td>{formatRate(variant.cartToPurchaseRate)}</td>
                  <td>{formatMatchTypeLabel(variant.matchedBy)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {callouts.length > 0 && (
        <div className="growth-audit-ga4-funnel__variants-callouts">
          {callouts.map((callout) => (
            <p key={callout} className="growth-audit-ga4-funnel__variants-callout">
              {callout}
            </p>
          ))}
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
          {funnelMeta.matchDebug &&
            renderMatchDebugBlock(funnelMeta.matchDebug, funnelMeta.matchedItemIds)}

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

          {renderVariantPerformanceSection(funnelMeta)}
        </>
      ) : (
        <p className="growth-audit-ga4-funnel__empty">
          Questa pagina non ha ancora dati funnel ecommerce GA4 nella run attuale.
        </p>
      )}
    </section>
  );
}
