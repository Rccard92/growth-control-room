import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { INTEGRATIONS } from "@gcr/shared";
import { IntegrationCard } from "./IntegrationCard";

const { integrationBrandIconsMock } = vi.hoisted(() => ({
  integrationBrandIconsMock: {
    shopify: "/assets/integrations/shopify.svg",
  } as Record<string, string>,
}));

vi.mock("./integrationBrandIcons", () => ({
  INTEGRATION_BRAND_ICONS: integrationBrandIconsMock,
}));

function renderCard(provider: (typeof INTEGRATIONS)[number]["provider"]) {
  const meta = INTEGRATIONS.find((item) => item.provider === provider)!;
  return renderToStaticMarkup(
    <IntegrationCard meta={meta} status="connected" actionLabel="Gestisci" />,
  );
}

describe("IntegrationCard brand icons", () => {
  it("renders img when provider has an SVG mapping", () => {
    const html = renderCard("shopify");
    expect(html).toContain("integration-card__brand-icon");
    expect(html).toContain("<img");
    expect(html).toContain('src="/assets/integrations/shopify.svg"');
    expect(html).not.toContain("integration-card__emoji-icon");
  });

  it("renders emoji fallback when provider has no SVG mapping", () => {
    const html = renderCard("klaviyo");
    expect(html).toContain("integration-card__emoji-icon");
    expect(html).toContain("✉️");
    expect(html).not.toContain("integration-card__brand-icon");
  });
});
