import type { ShopifyAttributionReadiness } from "@gcr/shared";

interface AttributionReadinessPanelProps {
  attribution: ShopifyAttributionReadiness;
  shopifyConnected: boolean;
}

const SOURCES = [
  { id: "shopify", label: "Shopify", status: "connected" as const },
  { id: "ga4", label: "GA4", status: "coming_soon" as const },
  { id: "meta", label: "Meta Ads", status: "coming_soon" as const },
  { id: "google", label: "Google Ads", status: "coming_soon" as const },
  { id: "klaviyo", label: "Klaviyo", status: "coming_soon" as const },
];

export function AttributionReadinessPanel({
  attribution,
  shopifyConnected,
}: AttributionReadinessPanelProps) {
  return (
    <section className="shopify-attribution gcr-card">
      <h3 className="shopify-panel__title">Marketing Attribution</h3>
      <p className="shopify-attribution__copy">
        Collega GA4, Meta Ads, Google Ads e Klaviyo per vedere source, medium, campaign, UTM,
        ROAS, CPA e revenue attribuita.
      </p>
      <p className="shopify-attribution__message">{attribution.message}</p>
      <ul className="shopify-attribution__sources">
        {SOURCES.map((source) => {
          const isConnected = source.id === "shopify" && shopifyConnected;
          const isComingSoon = source.status === "coming_soon";
          return (
            <li key={source.id} className="shopify-attribution__source">
              <span>{source.label}</span>
              <span
                className={`shopify-attribution__status ${
                  isConnected
                    ? "shopify-attribution__status--connected"
                    : isComingSoon
                      ? "shopify-attribution__status--soon"
                      : ""
                }`}
              >
                {isConnected ? "Connesso" : isComingSoon ? "Coming soon" : "Non connesso"}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
