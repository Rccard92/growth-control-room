import { describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { GoogleMerchantCenterAccountModal } from "./GoogleMerchantCenterAccountModal";

const {
  useMerchantAccountsMock,
  useSelectMerchantAccountMock,
} = vi.hoisted(() => ({
  useMerchantAccountsMock: vi.fn(),
  useSelectMerchantAccountMock: vi.fn(),
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
  useMerchantAccounts: useMerchantAccountsMock,
  useSelectMerchantAccount: useSelectMerchantAccountMock,
}));

function setupMocks() {
  useMerchantAccountsMock.mockReturnValue({
    data: {
      accounts: [
        {
          accountId: "123456",
          name: "accounts/123456",
          displayName: "Example Merchant",
          type: "STANDARD",
        },
      ],
    },
    isLoading: false,
    isError: false,
  });
  useSelectMerchantAccountMock.mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({
      accountId: "123456",
      message: "Account Merchant Center salvato.",
    }),
    isPending: false,
  });
}

describe("GoogleMerchantCenterAccountModal", () => {
  it("returns null when closed", () => {
    setupMocks();
    const html = renderToStaticMarkup(
      <GoogleMerchantCenterAccountModal
        projectId="proj-1"
        open={false}
        onClose={vi.fn()}
      />,
    );
    expect(html).toBe("");
  });

  it("renders dialog with account list when open", () => {
    setupMocks();
    const html = renderToStaticMarkup(
      <GoogleMerchantCenterAccountModal
        projectId="proj-1"
        selectedAccountId="123456"
        open
        onClose={vi.fn()}
      />,
    );
    expect(html).toContain('role="dialog"');
    expect(html).toContain("Seleziona account Merchant Center");
    expect(html).toContain("merchant-account-modal__option");
    expect(html).toContain("Example Merchant");
    expect(html).not.toContain("<select");
    expect(html).toContain("Salva account");
  });
});
