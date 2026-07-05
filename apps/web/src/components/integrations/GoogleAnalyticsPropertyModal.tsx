import { useEffect, useState } from "react";
import type { GoogleAnalyticsProperty } from "@gcr/shared";
import { AppModal } from "../ui/AppModal";
import {
  useGoogleAnalyticsProperties,
  useSelectGoogleAnalyticsProperty,
} from "../../hooks/useGoogleIntegrations";

interface GoogleAnalyticsPropertyModalProps {
  projectId: string;
  selectedPropertyId?: string | null;
  selectedPropertyName?: string | null;
  open: boolean;
  onClose: () => void;
}

export function GoogleAnalyticsPropertyModal({
  projectId,
  selectedPropertyId,
  selectedPropertyName,
  open,
  onClose,
}: GoogleAnalyticsPropertyModalProps) {
  const [selectedProperty, setSelectedProperty] = useState<GoogleAnalyticsProperty | null>(null);
  const propertiesQuery = useGoogleAnalyticsProperties(projectId, open);
  const selectProperty = useSelectGoogleAnalyticsProperty(projectId);

  useEffect(() => {
    if (!open) return;
    if (!selectedPropertyId) {
      setSelectedProperty(null);
      return;
    }
    const match = (propertiesQuery.data?.properties ?? []).find(
      (property) => property.propertyId === selectedPropertyId,
    );
    if (match) {
      setSelectedProperty(match);
      return;
    }
    if (selectedPropertyName) {
      setSelectedProperty({
        propertyId: selectedPropertyId,
        propertyName: `properties/${selectedPropertyId}`,
        displayName: selectedPropertyName,
      });
    }
  }, [open, selectedPropertyId, selectedPropertyName, propertiesQuery.data?.properties]);

  async function handleSave() {
    if (!selectedProperty) return;
    try {
      await selectProperty.mutateAsync({
        propertyId: selectedProperty.propertyId,
        propertyName: selectedProperty.propertyName,
        displayName: selectedProperty.displayName,
      });
      onClose();
    } catch {
      // Keep modal open on error.
    }
  }

  const properties = propertiesQuery.data?.properties ?? [];

  return (
    <AppModal
      open={open}
      onClose={onClose}
      title="Seleziona proprietà Google Analytics 4"
      subtitle="Scegli la proprietà GA4 da usare per analizzare traffico, engagement e conversioni delle landing page."
      maxWidth="md"
      footer={
        <div className="gsc-property-modal__footer">
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            onClick={onClose}
            disabled={selectProperty.isPending}
          >
            Annulla
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={!selectedProperty || selectProperty.isPending}
            onClick={() => void handleSave()}
          >
            {selectProperty.isPending ? "Salvataggio…" : "Salva proprietà"}
          </button>
        </div>
      }
    >
      {propertiesQuery.isLoading ? (
        <p className="gsc-property-modal__status">Caricamento proprietà…</p>
      ) : propertiesQuery.isError ? (
        <p className="gcr-alert gcr-alert--error">
          Impossibile caricare le proprietà Google Analytics 4.
        </p>
      ) : properties.length === 0 ? (
        <p className="gsc-property-modal__status">
          Nessuna proprietà GA4 trovata per questo account Google.
        </p>
      ) : (
        <div className="gsc-property-modal__list" role="listbox" aria-label="Proprietà GA4">
          {properties.map((property) => {
            const isSelected = selectedProperty?.propertyId === property.propertyId;
            return (
              <button
                key={property.propertyId}
                type="button"
                role="option"
                aria-selected={isSelected}
                className={`gsc-property-modal__option${isSelected ? " gsc-property-modal__option--selected" : ""}`}
                onClick={() => setSelectedProperty(property)}
              >
                <span className="gsc-property-modal__option-check" aria-hidden="true">
                  {isSelected ? "✓" : ""}
                </span>
                <span className="gsc-property-modal__option-body">
                  <span className="gsc-property-modal__option-main">{property.displayName}</span>
                  {property.accountDisplayName && (
                    <span className="gsc-property-modal__permission">{property.accountDisplayName}</span>
                  )}
                  <span className="gsc-property-modal__permission">{property.propertyId}</span>
                </span>
              </button>
            );
          })}
        </div>
      )}
    </AppModal>
  );
}
