import { FormEvent, useEffect, useRef, useState } from "react";
import type {
  BrandProductKnowledgeGeneral,
  BrandProductKnowledgeGeneralImportResponse,
  BrandProductKnowledgeGeneralProposal,
  BrandProductKnowledgeItem,
  BrandProductKnowledgeShopifyProductOption,
  ModuleCompletionStatus,
} from "@gcr/shared";
import { SeoEditModal } from "../content/optimizer/SeoEditModal";
import {
  useApplyProductKnowledgeGeneralProposal,
  useCreateProductKnowledgeItemFromShopify,
  useDeleteProductKnowledgeItem,
  useImportProductKnowledgeGeneralFromFile,
  useProductKnowledgeGeneral,
  useProductKnowledgeItems,
  useProductKnowledgeShopifyProducts,
  useUpdateProductKnowledgeGeneral,
  useUpdateProductKnowledgeItem,
} from "../../hooks/useBrandIntelligence";

interface BrandProductKnowledgePanelProps {
  projectId: string;
}

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.txt,.md";

const GENERAL_LIST_FIELDS = [
  ["generalPrinciples", "Principi generali (uno per riga)"],
  ["commonStrengths", "Punti di forza comuni (uno per riga)"],
  ["commonQualityRules", "Regole qualità comuni (uno per riga)"],
  ["commonProductionNotes", "Note produzione comuni (uno per riga)"],
  ["commonUsageNotes", "Note uso comuni (uno per riga)"],
  ["commonObjections", "Obiezioni comuni (uno per riga)"],
  ["communicationRules", "Regole comunicazione prodotto (uno per riga)"],
  ["productStorytellingRules", "Regole storytelling prodotto (uno per riga)"],
] as const;

type GeneralListKey = (typeof GENERAL_LIST_FIELDS)[number][0];

const STATUS_LABELS: Record<ModuleCompletionStatus, string> = {
  complete: "Completo",
  partial: "Parziale",
  empty: "Da completare",
};

function linesToList(text: string): string[] {
  return text.split("\n").map((l) => l.trim()).filter(Boolean);
}

function listToLines(list: string[] | null | undefined): string {
  return (list ?? []).join("\n");
}

function faqToLines(faq: Array<{ question: string; answer: string }> | null | undefined): string {
  return (faq ?? []).map((e) => `${e.question} | ${e.answer}`).join("\n");
}

function linesToFaq(text: string): Array<{ question: string; answer: string }> {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [q, ...rest] = line.split("|");
      return { question: (q ?? "").trim(), answer: rest.join("|").trim() };
    })
    .filter((e) => e.question);
}

function generalToForm(g: BrandProductKnowledgeGeneral): Partial<BrandProductKnowledgeGeneral> {
  return {
    generalPrinciples: g.generalPrinciples ?? [],
    commonStrengths: g.commonStrengths ?? [],
    commonQualityRules: g.commonQualityRules ?? [],
    commonProductionNotes: g.commonProductionNotes ?? [],
    commonUsageNotes: g.commonUsageNotes ?? [],
    commonObjections: g.commonObjections ?? [],
    commonFaq: g.commonFaq ?? [],
    communicationRules: g.communicationRules ?? [],
    productStorytellingRules: g.productStorytellingRules ?? [],
    notes: g.notes ?? "",
  };
}

function itemToForm(item: BrandProductKnowledgeItem): Partial<BrandProductKnowledgeItem> {
  return { ...item };
}

function renderGeneralFields(
  values: Partial<BrandProductKnowledgeGeneral>,
  onChange: (next: Partial<BrandProductKnowledgeGeneral>) => void,
  idPrefix: string,
) {
  return (
    <div className="bi-form-grid">
      {GENERAL_LIST_FIELDS.map(([key, label]) => (
        <div className="gcr-field bi-form-grid--full" key={key}>
          <label htmlFor={`${idPrefix}-${key}`}>{label}</label>
          <textarea
            id={`${idPrefix}-${key}`}
            rows={3}
            value={listToLines(values[key as GeneralListKey] as string[] | undefined)}
            onChange={(e) => onChange({ ...values, [key]: linesToList(e.target.value) })}
          />
        </div>
      ))}
      <div className="gcr-field bi-form-grid--full">
        <label htmlFor={`${idPrefix}-commonFaq`}>FAQ comuni (Domanda | Risposta, una per riga)</label>
        <textarea
          id={`${idPrefix}-commonFaq`}
          rows={4}
          value={faqToLines(values.commonFaq as Array<{ question: string; answer: string }> | undefined)}
          onChange={(e) => onChange({ ...values, commonFaq: linesToFaq(e.target.value) })}
        />
      </div>
      <div className="gcr-field bi-form-grid--full">
        <label htmlFor={`${idPrefix}-notes`}>Note</label>
        <textarea
          id={`${idPrefix}-notes`}
          rows={3}
          value={values.notes ?? ""}
          onChange={(e) => onChange({ ...values, notes: e.target.value })}
        />
      </div>
    </div>
  );
}

function ProductItemAccordion({
  projectId,
  item,
  expanded,
  onToggle,
}: {
  projectId: string;
  item: BrandProductKnowledgeItem;
  expanded: boolean;
  onToggle: () => void;
}) {
  const update = useUpdateProductKnowledgeItem(projectId);
  const remove = useDeleteProductKnowledgeItem(projectId);
  const [form, setForm] = useState<Partial<BrandProductKnowledgeItem>>(itemToForm(item));
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setForm(itemToForm(item));
  }, [item]);

  function handleSave(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    update.mutate(
      {
        itemId: item.id,
        data: {
          productName: form.productName,
          productLine: form.productLine || undefined,
          priority: form.priority || undefined,
          strategicDescription: form.strategicDescription || undefined,
          origin: form.origin || undefined,
          ingredients: form.ingredients || undefined,
          productionProcess: form.productionProcess || undefined,
          tasteNotes: form.tasteNotes || undefined,
          colorNotes: form.colorNotes || undefined,
          textureNotes: form.textureNotes || undefined,
          usageSuggestions: form.usageSuggestions || undefined,
          conservation: form.conservation || undefined,
          targetAudience: form.targetAudience || undefined,
          objections: form.objections?.length ? form.objections : undefined,
          faq: form.faq?.length ? form.faq : undefined,
          allowedClaims: form.allowedClaims?.length ? form.allowedClaims : undefined,
          forbiddenClaims: form.forbiddenClaims?.length ? form.forbiddenClaims : undefined,
          seoNotes: form.seoNotes || undefined,
          adsSocialNotes: form.adsSocialNotes || undefined,
          relatedProducts: form.relatedProducts?.length ? form.relatedProducts : undefined,
        },
      },
      {
        onSuccess: () => setMsg("Scheda prodotto salvata."),
        onError: (e: Error) => setErr(e.message),
      },
    );
  }

  const status = item.completionStatus ?? "empty";

  return (
    <article className={`bi-accordion gcr-card bi-accordion--${status}`}>
      <header className="bi-accordion__header">
        <button type="button" className="bi-accordion__toggle" onClick={onToggle}>
          <span className="bi-accordion__title">{item.productName}</span>
          <span className="bi-accordion__meta">
            {item.shopifyHandle && <span>@{item.shopifyHandle}</span>}
            {item.priority && <span> · {item.priority}</span>}
          </span>
          <span className={`bi-module-badge bi-module-badge--${status}`}>
            {STATUS_LABELS[status]}
          </span>
        </button>
        <div className="bi-accordion__actions">
          <button type="button" className="gcr-btn gcr-btn--sm" onClick={onToggle}>
            Modifica
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--sm gcr-btn--danger"
            disabled={remove.isPending}
            onClick={() => {
              if (window.confirm(`Rimuovere la scheda "${item.productName}"?`)) {
                remove.mutate(item.id);
              }
            }}
          >
            Rimuovi
          </button>
        </div>
      </header>
      {expanded && (
        <div className="bi-accordion__body">
          {err && <div className="gcr-alert gcr-alert--error">{err}</div>}
          {msg && <div className="gcr-alert gcr-alert--success">{msg}</div>}
          <form onSubmit={handleSave} className="bi-form-grid">
            <div className="gcr-field">
              <label>Nome prodotto</label>
              <input
                value={form.productName ?? ""}
                onChange={(e) => setForm({ ...form, productName: e.target.value })}
              />
            </div>
            <div className="gcr-field">
              <label>Linea prodotto</label>
              <input
                value={form.productLine ?? ""}
                onChange={(e) => setForm({ ...form, productLine: e.target.value })}
              />
            </div>
            <div className="gcr-field">
              <label>Priorità commerciale</label>
              <select
                value={form.priority ?? "medium"}
                onChange={(e) => setForm({ ...form, priority: e.target.value })}
              >
                <option value="high">Alta</option>
                <option value="medium">Media</option>
                <option value="low">Bassa</option>
              </select>
            </div>
            {(
              [
                ["strategicDescription", "Descrizione strategica", 4],
                ["origin", "Origine", 2],
                ["ingredients", "Ingredienti", 3],
                ["productionProcess", "Processo / lavorazione", 3],
                ["tasteNotes", "Gusto", 2],
                ["colorNotes", "Colore", 2],
                ["textureNotes", "Texture", 2],
                ["usageSuggestions", "Uso consigliato", 3],
                ["conservation", "Conservazione", 2],
                ["targetAudience", "Target", 2],
                ["seoNotes", "Note SEO", 3],
                ["adsSocialNotes", "Note ads/social", 3],
              ] as const
            ).map(([key, label, rows]) => (
              <div className="gcr-field bi-form-grid--full" key={key}>
                <label>{label}</label>
                <textarea
                  rows={rows}
                  value={(form[key] as string) ?? ""}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                />
              </div>
            ))}
            {(
              [
                ["objections", "Obiezioni (uno per riga)"],
                ["allowedClaims", "Claim consentiti (uno per riga)"],
                ["forbiddenClaims", "Claim vietati (uno per riga)"],
                ["relatedProducts", "Prodotti correlati (uno per riga)"],
              ] as const
            ).map(([key, label]) => (
              <div className="gcr-field bi-form-grid--full" key={key}>
                <label>{label}</label>
                <textarea
                  rows={3}
                  value={listToLines(form[key] as string[] | undefined)}
                  onChange={(e) => setForm({ ...form, [key]: linesToList(e.target.value) })}
                />
              </div>
            ))}
            <div className="gcr-field bi-form-grid--full">
              <label>FAQ (Domanda | Risposta, una per riga)</label>
              <textarea
                rows={4}
                value={faqToLines(form.faq as Array<{ question: string; answer: string }> | undefined)}
                onChange={(e) => setForm({ ...form, faq: linesToFaq(e.target.value) })}
              />
            </div>
            <div className="bi-profile-block__actions">
              <button type="submit" className="gcr-btn gcr-btn--primary" disabled={update.isPending}>
                {update.isPending ? "Salvataggio…" : "Salva scheda"}
              </button>
            </div>
          </form>
        </div>
      )}
    </article>
  );
}

export function BrandProductKnowledgePanel({ projectId }: BrandProductKnowledgePanelProps) {
  const { data: general, isLoading: generalLoading } = useProductKnowledgeGeneral(projectId);
  const { data: items = [], isLoading: itemsLoading } = useProductKnowledgeItems(projectId);
  const updateGeneral = useUpdateProductKnowledgeGeneral(projectId);
  const importFile = useImportProductKnowledgeGeneralFromFile(projectId);
  const applyProposal = useApplyProductKnowledgeGeneralProposal(projectId);
  const createFromShopify = useCreateProductKnowledgeItemFromShopify(projectId);

  const [generalForm, setGeneralForm] = useState<Partial<BrandProductKnowledgeGeneral>>({});
  const [proposal, setProposal] = useState<BrandProductKnowledgeGeneralProposal | null>(null);
  const [importResult, setImportResult] = useState<BrandProductKnowledgeGeneralImportResponse | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [shopifyModalOpen, setShopifyModalOpen] = useState(false);
  const [shopifySearch, setShopifySearch] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const { data: shopifyData, isLoading: shopifyLoading } = useProductKnowledgeShopifyProducts(
    projectId,
    shopifyModalOpen,
  );

  useEffect(() => {
    if (!general) return;
    setGeneralForm(generalToForm(general));
  }, [general]);

  function handleSaveGeneral(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    updateGeneral.mutate(
      {
        generalPrinciples: generalForm.generalPrinciples?.length
          ? generalForm.generalPrinciples
          : undefined,
        commonStrengths: generalForm.commonStrengths?.length ? generalForm.commonStrengths : undefined,
        commonQualityRules: generalForm.commonQualityRules?.length
          ? generalForm.commonQualityRules
          : undefined,
        commonProductionNotes: generalForm.commonProductionNotes?.length
          ? generalForm.commonProductionNotes
          : undefined,
        commonUsageNotes: generalForm.commonUsageNotes?.length
          ? generalForm.commonUsageNotes
          : undefined,
        commonObjections: generalForm.commonObjections?.length
          ? generalForm.commonObjections
          : undefined,
        commonFaq: generalForm.commonFaq?.length ? generalForm.commonFaq : undefined,
        communicationRules: generalForm.communicationRules?.length
          ? generalForm.communicationRules
          : undefined,
        productStorytellingRules: generalForm.productStorytellingRules?.length
          ? generalForm.productStorytellingRules
          : undefined,
        notes: generalForm.notes || undefined,
      },
      {
        onSuccess: () => setSuccessMessage("Regole generali salvate."),
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  function handleGenerateProposal() {
    if (!selectedFile) {
      setError("Seleziona un file prima di generare la proposta.");
      return;
    }
    setError(null);
    importFile.mutate(selectedFile, {
      onSuccess: (res) => {
        setImportResult(res);
        setProposal({ ...res.proposal });
      },
      onError: (err: Error) => setError(err.message),
    });
  }

  function handleApplyProposal() {
    if (!proposal) return;
    applyProposal.mutate(
      { proposal },
      {
        onSuccess: (data) => {
          setGeneralForm(generalToForm(data.general));
          setSuccessMessage(data.message);
          setProposal(null);
          setImportResult(null);
          setSelectedFile(null);
          if (fileInputRef.current) fileInputRef.current.value = "";
        },
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  function handleSelectShopifyProduct(product: BrandProductKnowledgeShopifyProductOption) {
    if (product.hasKnowledgeItem) return;
    createFromShopify.mutate(
      { shopifyProductId: product.id },
      {
        onSuccess: (item) => {
          setShopifyModalOpen(false);
          setExpandedId(item.id);
          setSuccessMessage(`Scheda creata per "${item.productName}".`);
        },
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  const filteredShopify = (shopifyData?.products ?? []).filter((p) => {
    const q = shopifySearch.toLowerCase();
    return (
      !q
      || p.title.toLowerCase().includes(q)
      || p.handle.toLowerCase().includes(q)
    );
  });

  if (generalLoading) return <p className="bi-panel__subtitle">Caricamento…</p>;

  return (
    <div className="bi-profile-v1">
      {error && <div className="gcr-alert gcr-alert--error" style={{ marginBottom: "1rem" }}>{error}</div>}
      {successMessage && (
        <div className="gcr-alert gcr-alert--success" style={{ marginBottom: "1rem" }}>
          {successMessage}
        </div>
      )}

      <section className="bi-profile-block gcr-card">
        <h3 className="bi-panel__title">Regole generali prodotti</h3>
        <p className="bi-panel__subtitle">
          Knowledge valida per tutti i prodotti. L&apos;import da file genera solo regole generali,
          non schede prodotto specifiche.
        </p>

        <div
          className="bi-dropzone"
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === "Enter" && fileInputRef.current?.click()}
        >
          <p className="bi-dropzone__title">Importa da file</p>
          <p className="bi-dropzone__hint">PDF, DOCX, TXT o MD — max 15 MB</p>
          {selectedFile && <p>Selezionato: <strong>{selectedFile.name}</strong></p>}
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_EXTENSIONS}
            style={{ display: "none" }}
            onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <div className="bi-profile-block__actions">
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={importFile.isPending || !selectedFile}
            onClick={handleGenerateProposal}
          >
            {importFile.isPending ? "Generazione…" : "Genera proposta AI"}
          </button>
        </div>
      </section>

      {proposal && (
        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Proposta AI (anteprima)</h3>
          {importResult && (
            <p className="bi-panel__subtitle">
              Confidenza: {(importResult.confidence * 100).toFixed(0)}%
              {importResult.warnings.length > 0 && <> — {importResult.warnings.join(" ")}</>}
            </p>
          )}
          {renderGeneralFields(
            proposal as Partial<BrandProductKnowledgeGeneral>,
            (next) =>
              setProposal({
                generalPrinciples: next.generalPrinciples,
                commonStrengths: next.commonStrengths,
                commonQualityRules: next.commonQualityRules,
                commonProductionNotes: next.commonProductionNotes,
                commonUsageNotes: next.commonUsageNotes,
                commonObjections: next.commonObjections,
                commonFaq: next.commonFaq as Array<{ question: string; answer: string }> | null,
                communicationRules: next.communicationRules,
                productStorytellingRules: next.productStorytellingRules,
                notes: next.notes,
              }),
            "proposal",
          )}
          <div className="bi-profile-block__actions">
            <button
              type="button"
              className="gcr-btn gcr-btn--primary"
              disabled={applyProposal.isPending}
              onClick={handleApplyProposal}
            >
              {applyProposal.isPending ? "Applicazione…" : "Applica proposta"}
            </button>
          </div>
        </section>
      )}

      <section className="bi-profile-block gcr-card">
        <h3 className="bi-panel__title">Regole generali ufficiali</h3>
        <form onSubmit={handleSaveGeneral}>
          {renderGeneralFields(generalForm, setGeneralForm, "official")}
          <div className="bi-profile-block__actions">
            <button type="submit" className="gcr-btn gcr-btn--primary" disabled={updateGeneral.isPending}>
              {updateGeneral.isPending ? "Salvataggio…" : "Salva regole generali"}
            </button>
          </div>
        </form>
      </section>

      <section className="bi-profile-block gcr-card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
          <div>
            <h3 className="bi-panel__title">Schede prodotto specifiche</h3>
            <p className="bi-panel__subtitle">
              Collega prodotti Shopify reali e compila knowledge dedicata per ciascuno.
            </p>
          </div>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            onClick={() => setShopifyModalOpen(true)}
          >
            Aggiungi prodotto da Shopify
          </button>
        </div>

        {itemsLoading && <p className="bi-panel__subtitle">Caricamento schede…</p>}
        {!itemsLoading && items.length === 0 && (
          <p className="bi-panel__subtitle" style={{ marginTop: "1rem" }}>
            Nessuna scheda prodotto. Aggiungi un prodotto da Shopify per iniziare.
          </p>
        )}
        <div className="bi-accordion-list" style={{ marginTop: "1rem" }}>
          {items.map((item) => (
            <ProductItemAccordion
              key={item.id}
              projectId={projectId}
              item={item}
              expanded={expandedId === item.id}
              onToggle={() => setExpandedId(expandedId === item.id ? null : item.id)}
            />
          ))}
        </div>
      </section>

      <SeoEditModal
        open={shopifyModalOpen}
        onClose={() => setShopifyModalOpen(false)}
        title="Seleziona prodotto Shopify"
      >
        {!shopifyData?.shopifyConnected && !shopifyLoading && (
          <p className="bi-panel__subtitle">
            {shopifyData?.message
              ?? "Collega e sincronizza Shopify per selezionare prodotti reali."}
          </p>
        )}
        {shopifyData?.shopifyConnected && (
          <>
            <input
              type="search"
              placeholder="Cerca per titolo o handle…"
              value={shopifySearch}
              onChange={(e) => setShopifySearch(e.target.value)}
              style={{ width: "100%", marginBottom: "1rem" }}
            />
            <ul className="bi-shopify-picker-list">
              {filteredShopify.map((p) => (
                <li key={p.id} className="bi-shopify-picker-item">
                  {p.featuredImageUrl && (
                    <img src={p.featuredImageUrl} alt="" width={40} height={40} />
                  )}
                  <div className="bi-shopify-picker-item__info">
                    <strong>{p.title}</strong>
                    <span>@{p.handle}</span>
                    {p.productType && <span> · {p.productType}</span>}
                  </div>
                  <button
                    type="button"
                    className="gcr-btn gcr-btn--sm gcr-btn--primary"
                    disabled={p.hasKnowledgeItem || createFromShopify.isPending}
                    onClick={() => handleSelectShopifyProduct(p)}
                  >
                    {p.hasKnowledgeItem ? "Già aggiunto" : "Seleziona"}
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </SeoEditModal>
    </div>
  );
}
