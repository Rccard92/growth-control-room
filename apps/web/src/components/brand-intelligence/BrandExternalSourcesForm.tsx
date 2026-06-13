import { useEffect, useState } from "react";
import type {
  BrandExternalSourceInput,
  BrandExternalSourcesFormValues,
  ExternalSourceType,
} from "@gcr/shared";

const EMPTY_VALUES: BrandExternalSourcesFormValues = {
  brandName: "",
  websiteUrl: "",
  instagramUrl: "",
  facebookUrl: "",
  tiktokUrl: "",
  youtubeUrl: "",
  linkedinUrl: "",
  trustpilotUrl: "",
  googleBusinessUrl: "",
  otherSources: [],
};

const SOCIAL_FIELDS: Array<{
  key: keyof BrandExternalSourcesFormValues;
  label: string;
  sourceType: ExternalSourceType;
}> = [
  { key: "instagramUrl", label: "Instagram URL", sourceType: "instagram" },
  { key: "facebookUrl", label: "Facebook URL", sourceType: "facebook" },
  { key: "tiktokUrl", label: "TikTok URL", sourceType: "tiktok" },
  { key: "youtubeUrl", label: "YouTube URL", sourceType: "youtube" },
  { key: "linkedinUrl", label: "LinkedIn URL", sourceType: "linkedin" },
  { key: "trustpilotUrl", label: "Trustpilot URL", sourceType: "trustpilot" },
  { key: "googleBusinessUrl", label: "Google Business Profile URL", sourceType: "google_business" },
];

interface BrandExternalSourcesFormProps {
  initialBrandName?: string;
  initialWebsiteUrl?: string;
  onChange?: (values: BrandExternalSourcesFormValues, sources: BrandExternalSourceInput[]) => void;
}

export function buildExternalSourcesFromForm(
  values: BrandExternalSourcesFormValues,
): BrandExternalSourceInput[] {
  const sources: BrandExternalSourceInput[] = [];

  for (const field of SOCIAL_FIELDS) {
    const url = String(values[field.key] ?? "").trim();
    if (url) {
      sources.push({ sourceType: field.sourceType, url });
    }
  }

  for (const other of values.otherSources) {
    const url = other.url.trim();
    if (!url) continue;
    sources.push({
      sourceType: "other",
      url,
      label: other.label.trim() || undefined,
    });
  }

  return sources;
}

export function BrandExternalSourcesForm({
  initialBrandName = "",
  initialWebsiteUrl = "",
  onChange,
}: BrandExternalSourcesFormProps) {
  const [values, setValues] = useState<BrandExternalSourcesFormValues>({
    ...EMPTY_VALUES,
    brandName: initialBrandName,
    websiteUrl: initialWebsiteUrl,
  });

  useEffect(() => {
    setValues((prev) => ({
      ...prev,
      brandName: initialBrandName || prev.brandName,
      websiteUrl: initialWebsiteUrl || prev.websiteUrl,
    }));
  }, [initialBrandName, initialWebsiteUrl]);

  useEffect(() => {
    onChange?.(values, buildExternalSourcesFromForm(values));
  }, [values, onChange]);

  function update<K extends keyof BrandExternalSourcesFormValues>(
    key: K,
    value: BrandExternalSourcesFormValues[K],
  ) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  function addOtherSource() {
    setValues((prev) => ({
      ...prev,
      otherSources: [...prev.otherSources, { label: "", url: "" }],
    }));
  }

  function updateOtherSource(index: number, field: "label" | "url", value: string) {
    setValues((prev) => ({
      ...prev,
      otherSources: prev.otherSources.map((item, i) =>
        i === index ? { ...item, [field]: value } : item,
      ),
    }));
  }

  function removeOtherSource(index: number) {
    setValues((prev) => ({
      ...prev,
      otherSources: prev.otherSources.filter((_, i) => i !== index),
    }));
  }

  return (
    <section className="bi-external-sources">
      <h3 className="bi-panel__title">Fonti brand</h3>
      <p className="bi-panel__subtitle">
        Queste fonti aiutano l&apos;AI a completare le informazioni mancanti dai file. Ogni dato
        estratto resterà in bozza e dovrà essere approvato.
      </p>

      <div className="bi-form-grid">
        <label className="gcr-field">
          <span>Brand name</span>
          <input
            type="text"
            value={values.brandName}
            onChange={(e) => update("brandName", e.target.value)}
            placeholder="Nome del brand"
          />
        </label>
        <label className="gcr-field">
          <span>Website URL</span>
          <input
            type="url"
            value={values.websiteUrl}
            onChange={(e) => update("websiteUrl", e.target.value)}
            placeholder="https://..."
          />
        </label>
      </div>

      <p className="bi-external-sources__hint">
        Obbligatorio almeno uno tra Brand name e Website URL (se non carichi file).
      </p>

      <div className="bi-form-grid bi-form-grid--2">
        {SOCIAL_FIELDS.map((field) => (
          <label key={field.key} className="gcr-field">
            <span>{field.label}</span>
            <input
              type="url"
              value={String(values[field.key] ?? "")}
              onChange={(e) => update(field.key, e.target.value)}
              placeholder="https://..."
            />
          </label>
        ))}
      </div>

      <div className="bi-external-sources__other">
        <div className="bi-external-sources__other-header">
          <h4>Altre fonti pubbliche</h4>
          <button type="button" className="gcr-btn gcr-btn--ghost gcr-btn--sm" onClick={addOtherSource}>
            + Aggiungi URL
          </button>
        </div>
        {values.otherSources.map((item, index) => (
          <div key={index} className="bi-external-sources__other-row">
            <input
              type="text"
              value={item.label}
              onChange={(e) => updateOtherSource(index, "label", e.target.value)}
              placeholder="Etichetta (opzionale)"
            />
            <input
              type="url"
              value={item.url}
              onChange={(e) => updateOtherSource(index, "url", e.target.value)}
              placeholder="https://..."
            />
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost gcr-btn--sm"
              onClick={() => removeOtherSource(index)}
            >
              Rimuovi
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
