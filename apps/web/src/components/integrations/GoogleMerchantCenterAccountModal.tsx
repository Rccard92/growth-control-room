import { useEffect, useState } from "react";
import type { GoogleMerchantAccount } from "@gcr/shared";
import { AppModal } from "../ui/AppModal";
import {
  useMerchantAccounts,
  useSelectMerchantAccount,
} from "../../hooks/useGoogleIntegrations";

interface GoogleMerchantCenterAccountModalProps {
  projectId: string;
  selectedAccountId?: string | null;
  open: boolean;
  onClose: () => void;
}

export function GoogleMerchantCenterAccountModal({
  projectId,
  selectedAccountId,
  open,
  onClose,
}: GoogleMerchantCenterAccountModalProps) {
  const [selectedId, setSelectedId] = useState(selectedAccountId ?? "");
  const accountsQuery = useMerchantAccounts(projectId, open);
  const selectAccount = useSelectMerchantAccount(projectId);

  useEffect(() => {
    if (!open) return;
    setSelectedId(selectedAccountId ?? "");
  }, [open, selectedAccountId]);

  async function handleSave() {
    const account = accounts.find((item: GoogleMerchantAccount) => item.accountId === selectedId);
    if (!account) return;
    try {
      await selectAccount.mutateAsync({
        accountId: account.accountId,
        accountName: account.displayName || account.name,
      });
      onClose();
    } catch {
      // Error surfaced by mutation / global handlers; keep modal open.
    }
  }

  const accounts = accountsQuery.data?.accounts ?? [];

  return (
    <AppModal
      open={open}
      onClose={onClose}
      title="Seleziona account Merchant Center"
      subtitle="Scegli l'account Merchant Center da usare per diagnosticare feed e visibilità Shopping nel Growth Audit."
      maxWidth="md"
      footer={
        <div className="merchant-account-modal__footer">
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            onClick={onClose}
            disabled={selectAccount.isPending}
          >
            Annulla
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={!selectedId || selectAccount.isPending}
            onClick={() => void handleSave()}
          >
            {selectAccount.isPending ? "Salvataggio…" : "Salva account"}
          </button>
        </div>
      }
    >
      {accountsQuery.isLoading ? (
        <p className="merchant-account-modal__status">Caricamento account…</p>
      ) : accountsQuery.isError ? (
        <p className="gcr-alert gcr-alert--error">
          Impossibile caricare gli account Merchant Center. Verifica OAuth Google e che Merchant
          API sia abilitata.
        </p>
      ) : accounts.length === 0 ? (
        <p className="merchant-account-modal__status">
          Nessun account Merchant Center trovato per questo account Google.
        </p>
      ) : (
        <div className="merchant-account-modal__list" role="listbox" aria-label="Account Merchant Center">
          {accounts.map((account: GoogleMerchantAccount) => {
            const isSelected = selectedId === account.accountId;
            return (
              <button
                key={account.accountId}
                type="button"
                role="option"
                aria-selected={isSelected}
                className={`merchant-account-modal__option${isSelected ? " merchant-account-modal__option--selected" : ""}`}
                onClick={() => setSelectedId(account.accountId)}
              >
                <span className="merchant-account-modal__option-check" aria-hidden="true">
                  {isSelected ? "✓" : ""}
                </span>
                <span className="merchant-account-modal__option-body">
                  <span className="merchant-account-modal__option-main">
                    {account.displayName || account.name}
                  </span>
                  <span className="merchant-account-modal__option-sub">
                    ID {account.accountId}
                    {account.type ? ` · ${account.type}` : ""}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      )}
    </AppModal>
  );
}
