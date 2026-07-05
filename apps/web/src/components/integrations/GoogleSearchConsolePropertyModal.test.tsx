import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { GoogleSearchConsolePropertyModal } from "./GoogleSearchConsolePropertyModal";

const {
  useSearchConsoleSitesMock,
  useSelectSearchConsoleSiteMock,
} = vi.hoisted(() => ({
  useSearchConsoleSitesMock: vi.fn(),
  useSelectSearchConsoleSiteMock: vi.fn(),
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
  useSearchConsoleSites: useSearchConsoleSitesMock,
  useSelectSearchConsoleSite: useSelectSearchConsoleSiteMock,
}));

function setupMocks() {
  useSearchConsoleSitesMock.mockReturnValue({
    data: {
      sites: [
        { siteUrl: "https://solmielato.it/", permissionLevel: "siteOwner" },
        { siteUrl: "sc-domain:solmielato.it", permissionLevel: "siteFullUser" },
      ],
    },
    isLoading: false,
    isError: false,
  });
  useSelectSearchConsoleSiteMock.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({
      siteUrl: "https://solmielato.it/",
      message: "Proprietà Search Console salvata.",
    }),
    isPending: false,
  });
}

describe("GoogleSearchConsolePropertyModal", () => {
  it("returns null when closed", () => {
    setupMocks();
    const html = renderToStaticMarkup(
      <GoogleSearchConsolePropertyModal
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
      <GoogleSearchConsolePropertyModal
        projectId="proj-1"
        selectedSiteUrl="https://solmielato.it/"
        open
        onClose={vi.fn()}
      />,
    );
    expect(html).toContain('role="dialog"');
    expect(html).toContain("Seleziona proprietà Search Console");
    expect(html).toContain("gsc-property-modal__option");
    expect(html).toContain("https://solmielato.it/");
    expect(html).toContain("siteOwner");
    expect(html).not.toContain("<select");
    expect(html).toContain("Salva proprietà");
  });
});
