import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { GoogleAnalyticsPropertyModal } from "./GoogleAnalyticsPropertyModal";

const {
  useGoogleAnalyticsPropertiesMock,
  useSelectGoogleAnalyticsPropertyMock,
} = vi.hoisted(() => ({
  useGoogleAnalyticsPropertiesMock: vi.fn(),
  useSelectGoogleAnalyticsPropertyMock: vi.fn(),
}));

vi.mock("../ui/AppModal", () => ({
  AppModal: ({
    open,
    title,
    subtitle,
    footer,
    children,
  }: {
    open: boolean;
    title: string;
    subtitle?: string;
    footer?: ReactNode;
    children: ReactNode;
  }) =>
    open ? (
      <div role="dialog" aria-modal="true">
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
        {children}
        {footer}
      </div>
    ) : null,
}));

vi.mock("../../hooks/useGoogleIntegrations", () => ({
  useGoogleAnalyticsProperties: useGoogleAnalyticsPropertiesMock,
  useSelectGoogleAnalyticsProperty: useSelectGoogleAnalyticsPropertyMock,
}));

function setupMocks() {
  useGoogleAnalyticsPropertiesMock.mockReturnValue({
    data: {
      properties: [
        {
          propertyId: "123456789",
          propertyName: "properties/123456789",
          displayName: "Solmielato GA4",
          accountDisplayName: "Solmielato Account",
        },
      ],
    },
    isLoading: false,
    isError: false,
  });
  useSelectGoogleAnalyticsPropertyMock.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({
      propertyId: "123456789",
      message: "Proprietà GA4 salvata.",
    }),
    isPending: false,
  });
}

describe("GoogleAnalyticsPropertyModal", () => {
  it("returns null when closed", () => {
    setupMocks();
    const html = renderToStaticMarkup(
      <GoogleAnalyticsPropertyModal
        projectId="proj-1"
        open={false}
        onClose={vi.fn()}
      />,
    );
    expect(html).toBe("");
  });

  it("renders dialog with custom property list when open", () => {
    setupMocks();
    const html = renderToStaticMarkup(
      <GoogleAnalyticsPropertyModal
        projectId="proj-1"
        selectedPropertyId="123456789"
        selectedPropertyName="Solmielato GA4"
        open
        onClose={vi.fn()}
      />,
    );
    expect(html).toContain('role="dialog"');
    expect(html).toContain("Seleziona proprietà Google Analytics 4");
    expect(html).toContain("gsc-property-modal__option");
    expect(html).toContain("Solmielato GA4");
    expect(html).toContain("123456789");
    expect(html).not.toContain("<select");
    expect(html).toContain("Salva proprietà");
  });
});
