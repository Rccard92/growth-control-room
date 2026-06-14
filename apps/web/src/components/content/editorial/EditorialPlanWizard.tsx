import { useMemo, useState } from "react";
import type {
  ContentSeoEditorialContentType,
  ContentSeoEditorialCommercialIntensity,
  ContentSeoEditorialFrequency,
  ContentSeoEditorialItem,
  ContentSeoEditorialObjective,
  EditorialPlanGenerateRequest,
  EditorialWeekday,
} from "@gcr/shared";
import {
  CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS,
  CONTENT_SEO_EDITORIAL_OBJECTIVE_LABELS,
} from "@gcr/shared";
import { AppModal } from "../../ui/AppModal";
import { AppSelect } from "../../ui/AppSelect";
import { useGenerateEditorialCalendar } from "../../../hooks/useContentSeoEditorial";
import { useShopifyProducts } from "../../../hooks/useShopify";

const ALL_CONTENT_TYPES = Object.keys(
  CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS,
) as ContentSeoEditorialContentType[];

const FREQUENCY_OPTIONS: { value: ContentSeoEditorialFrequency; label: string }[] = [
  { value: "daily", label: "Ogni giorno" },
  { value: "every_2_days", label: "Ogni 2 giorni" },
  { value: "every_3_days", label: "Ogni 3 giorni" },
  { value: "every_4_days", label: "Ogni 4 giorni" },
  { value: "weekly", label: "Settimanale" },
  { value: "twice_weekly", label: "Due volte a settimana" },
  { value: "custom", label: "Personalizzato" },
];

const WEEKDAY_OPTIONS: { value: EditorialWeekday; label: string }[] = [
  { value: "monday", label: "Lunedì" },
  { value: "tuesday", label: "Martedì" },
  { value: "wednesday", label: "Mercoledì" },
  { value: "thursday", label: "Giovedì" },
  { value: "friday", label: "Venerdì" },
  { value: "saturday", label: "Sabato" },
  { value: "sunday", label: "Domenica" },
];

const INTENSITY_OPTIONS: { value: ContentSeoEditorialCommercialIntensity; label: string }[] = [
  { value: "soft", label: "Soft" },
  { value: "balanced", label: "Bilanciata" },
  { value: "sales_oriented", label: "Orientata alle vendite" },
];

const OBJECTIVE_OPTIONS = Object.entries(CONTENT_SEO_EDITORIAL_OBJECTIVE_LABELS).map(
  ([value, label]) => ({ value, label }),
);

function defaultEndDate(): string {
  const d = new Date();
  d.setMonth(d.getMonth() + 1);
  return d.toISOString().slice(0, 10);
}

function defaultStartDate(): string {
  return new Date().toISOString().slice(0, 10);
}

interface EditorialPlanWizardProps {
  open: boolean;
  projectId: string;
  shopifyConnected: boolean;
  onClose: () => void;
  onConfirmed: () => void;
}

export function EditorialPlanWizard({
  open,
  projectId,
  shopifyConnected,
  onClose,
  onConfirmed,
}: EditorialPlanWizardProps) {
  const generateMutation = useGenerateEditorialCalendar(projectId);
  const productsQuery = useShopifyProducts(projectId, shopifyConnected);

  const [step, setStep] = useState(1);
  const [startDate, setStartDate] = useState(defaultStartDate);
  const [endDate, setEndDate] = useState(defaultEndDate);
  const [frequency, setFrequency] = useState<ContentSeoEditorialFrequency>("weekly");
  const [preferredWeekdays, setPreferredWeekdays] = useState<EditorialWeekday[]>(["tuesday", "thursday"]);
  const [contentTypes, setContentTypes] = useState<ContentSeoEditorialContentType[]>([
    "educational_article",
    "product_guide",
  ]);
  const [objective, setObjective] = useState<ContentSeoEditorialObjective>("seo_traffic");
  const [commercialIntensity, setCommercialIntensity] =
    useState<ContentSeoEditorialCommercialIntensity>("balanced");
  const [linkedProductIds, setLinkedProductIds] = useState<string[]>([]);
  const [avoidProductIds, setAvoidProductIds] = useState<string[]>([]);
  const [productSearch, setProductSearch] = useState("");
  const [primaryKeywords, setPrimaryKeywords] = useState("");
  const [notes, setNotes] = useState("");
  const [previewItems, setPreviewItems] = useState<ContentSeoEditorialItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const products = productsQuery.data ?? [];

  const filteredProducts = useMemo(() => {
    const q = productSearch.trim().toLowerCase();
    if (!q) return products;
    return products.filter((p) => p.title.toLowerCase().includes(q));
  }, [products, productSearch]);

  const needsWeekdays = frequency === "custom" || frequency === "twice_weekly";
  const stepSubtitle = `Step ${Math.min(step, 4)} di 4${step === 5 ? " — Anteprima" : ""}`;

  function buildRequest(): EditorialPlanGenerateRequest {
    return {
      startDate,
      endDate,
      frequency,
      preferredWeekdays: needsWeekdays ? preferredWeekdays : null,
      contentTypes,
      objective,
      commercialIntensity,
      linkedProductIds,
      avoidProductIds,
      primaryKeywords: primaryKeywords
        .split(",")
        .map((k) => k.trim())
        .filter(Boolean),
      notes: notes.trim() || undefined,
    };
  }

  function validateStep(): string | null {
    if (step === 1 || step === 5) {
      if (endDate < startDate) return "La data di fine deve essere uguale o successiva alla data di inizio.";
      if (needsWeekdays && preferredWeekdays.length === 0) {
        return "Seleziona almeno un giorno della settimana per questa frequenza.";
      }
    }
    if (step === 2 || step === 5) {
      if (contentTypes.length === 0) return "Seleziona almeno una tipologia di contenuto.";
    }
    return null;
  }

  function toggleContentType(type: ContentSeoEditorialContentType) {
    setContentTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type],
    );
  }

  function toggleWeekday(day: EditorialWeekday) {
    setPreferredWeekdays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day],
    );
  }

  function toggleProductId(id: string, list: "linked" | "avoid") {
    if (list === "linked") {
      setLinkedProductIds((prev) =>
        prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
      );
    } else {
      setAvoidProductIds((prev) =>
        prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
      );
    }
  }

  async function handlePreview() {
    const validationError = validateStep();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    try {
      const result = await generateMutation.mutateAsync({
        data: buildRequest(),
        dryRun: true,
      });
      setPreviewItems(result.items);
      setStep(5);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante l'anteprima.");
    }
  }

  async function handleConfirm() {
    const validationError = validateStep();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    try {
      await generateMutation.mutateAsync({
        data: buildRequest(),
        dryRun: false,
      });
      onConfirmed();
      handleClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore durante la creazione del piano.");
    }
  }

  function handleClose() {
    setStep(1);
    setPreviewItems([]);
    setError(null);
    onClose();
  }

  const footer = (
    <>
      {step > 1 && step < 5 && (
        <button type="button" className="gcr-btn gcr-btn--secondary" onClick={() => setStep(step - 1)}>
          Indietro
        </button>
      )}
      {step < 4 && (
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          onClick={() => {
            const validationError = validateStep();
            if (validationError) {
              setError(validationError);
              return;
            }
            setError(null);
            setStep(step + 1);
          }}
        >
          Avanti
        </button>
      )}
      {step === 4 && (
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          disabled={generateMutation.isPending}
          onClick={() => void handlePreview()}
        >
          Anteprima
        </button>
      )}
      {step === 5 && (
        <>
          <button type="button" className="gcr-btn gcr-btn--secondary" onClick={() => setStep(4)}>
            Modifica
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={generateMutation.isPending}
            onClick={() => void handleConfirm()}
          >
            Conferma piano
          </button>
        </>
      )}
    </>
  );

  return (
    <AppModal
      open={open}
      onClose={handleClose}
      title="Crea piano editoriale"
      subtitle={stepSubtitle}
      maxWidth="lg"
      footer={footer}
    >
      {error && <div className="gcr-alert gcr-alert--error">{error}</div>}

      {step === 1 && (
        <section className="editorial-wizard__body">
          <h4>Periodo e frequenza</h4>
          <label className="gcr-field">
            <span className="gcr-field__label">Data inizio</span>
            <input
              type="date"
              className="gcr-input"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </label>
          <label className="gcr-field">
            <span className="gcr-field__label">Data fine</span>
            <input
              type="date"
              className="gcr-input"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </label>
          <AppSelect
            label="Frequenza"
            value={frequency}
            options={FREQUENCY_OPTIONS}
            onChange={(v) => setFrequency(v as ContentSeoEditorialFrequency)}
          />
          {needsWeekdays && (
            <fieldset className="editorial-wizard__checkbox-group">
              <legend className="gcr-field__label">Giorni preferiti</legend>
              {WEEKDAY_OPTIONS.map((opt) => (
                <label key={opt.value} className="editorial-wizard__checkbox">
                  <input
                    type="checkbox"
                    checked={preferredWeekdays.includes(opt.value)}
                    onChange={() => toggleWeekday(opt.value)}
                  />
                  {opt.label}
                </label>
              ))}
            </fieldset>
          )}
        </section>
      )}

      {step === 2 && (
        <section className="editorial-wizard__body">
          <h4>Tipologie di contenuto</h4>
          <div className="editorial-wizard__checkbox-group">
            {ALL_CONTENT_TYPES.map((type) => (
              <label key={type} className="editorial-wizard__checkbox">
                <input
                  type="checkbox"
                  checked={contentTypes.includes(type)}
                  onChange={() => toggleContentType(type)}
                />
                {CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS[type]}
              </label>
            ))}
          </div>
        </section>
      )}

      {step === 3 && (
        <section className="editorial-wizard__body">
          <h4>Obiettivo e intensità commerciale</h4>
          <AppSelect
            label="Obiettivo"
            value={objective}
            options={OBJECTIVE_OPTIONS}
            onChange={(v) => setObjective(v as ContentSeoEditorialObjective)}
          />
          <AppSelect
            label="Intensità commerciale"
            value={commercialIntensity}
            options={INTENSITY_OPTIONS}
            onChange={(v) =>
              setCommercialIntensity(v as ContentSeoEditorialCommercialIntensity)
            }
          />
        </section>
      )}

      {step === 4 && (
        <section className="editorial-wizard__body">
          <h4>Prodotti, keyword e note</h4>
          {!shopifyConnected && (
            <p className="gcr-card__description editorial-wizard__shopify-hint">
              Shopify non connesso: puoi procedere senza collegare prodotti.
            </p>
          )}
          {shopifyConnected && (
            <>
              <label className="gcr-field">
                <span className="gcr-field__label">Cerca prodotti</span>
                <input
                  className="gcr-input"
                  value={productSearch}
                  onChange={(e) => setProductSearch(e.target.value)}
                  placeholder="Filtra per titolo…"
                />
              </label>
              <div className="editorial-wizard__product-lists">
                <div>
                  <p className="gcr-field__label">Prodotti da valorizzare</p>
                  <div className="editorial-wizard__product-scroll">
                    {filteredProducts.map((p) => (
                      <label key={`link-${p.id}`} className="editorial-wizard__checkbox">
                        <input
                          type="checkbox"
                          checked={linkedProductIds.includes(p.id)}
                          onChange={() => toggleProductId(p.id, "linked")}
                        />
                        {p.title}
                      </label>
                    ))}
                    {filteredProducts.length === 0 && (
                      <p className="gcr-card__description">Nessun prodotto trovato.</p>
                    )}
                  </div>
                </div>
                <div>
                  <p className="gcr-field__label">Prodotti da evitare</p>
                  <div className="editorial-wizard__product-scroll">
                    {filteredProducts.map((p) => (
                      <label key={`avoid-${p.id}`} className="editorial-wizard__checkbox">
                        <input
                          type="checkbox"
                          checked={avoidProductIds.includes(p.id)}
                          onChange={() => toggleProductId(p.id, "avoid")}
                        />
                        {p.title}
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
          <label className="gcr-field">
            <span className="gcr-field__label">Keyword principali (separate da virgola)</span>
            <input
              className="gcr-input"
              value={primaryKeywords}
              onChange={(e) => setPrimaryKeywords(e.target.value)}
            />
          </label>
          <label className="gcr-field">
            <span className="gcr-field__label">Note</span>
            <textarea
              className="gcr-input"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </label>
        </section>
      )}

      {step === 5 && (
        <section className="editorial-wizard__body">
          <h4>Anteprima piano ({previewItems.length} item)</h4>
          <ul className="editorial-wizard__preview-list">
            {previewItems.map((item) => (
              <li key={item.id}>
                <strong>{item.plannedDate.slice(0, 10)}</strong> — {item.title}
                <span className="editorial-wizard__preview-type">
                  {CONTENT_SEO_EDITORIAL_CONTENT_TYPE_LABELS[item.contentType]}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </AppModal>
  );
}
