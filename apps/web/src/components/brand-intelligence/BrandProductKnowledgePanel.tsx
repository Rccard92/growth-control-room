import { FormEvent, useEffect, useRef, useState } from "react";
import type {
  BrandProductKnowledgeGeneral,
  BrandProductKnowledgeGeneralImportResponse,
  BrandProductKnowledgeGeneralProposal,
  BrandProductKnowledgeItem,
  BrandProductKnowledgeItemProposal,
  BrandProductKnowledgeItemsImportResponse,
  BrandProductKnowledgeShopifyProductOption,
  ModuleCompletionStatus,
} from "@gcr/shared";
import { SeoEditModal } from "../content/optimizer/SeoEditModal";
import {
  useApplyProductKnowledgeGeneralProposal,
  useApplyProductKnowledgeItemsImportProposal,
  useCreateProductKnowledgeItemFromShopify,
  useDeleteProductKnowledgeItem,
  useImportProductKnowledgeGeneralFromFile,
  useImportProductKnowledgeItemsFromFile,
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

const MISSING_FIELD_LABELS: Record<string, string> = {
  productLine: "Categoria / linea",
  strategicDescription: "Descrizione strategica",
  origin: "Origine",
  ingredients: "Ingredienti",
  productionProcess: "Processo / lavorazione",
  tasteNotes: "Gusto / profumo",
  colorNotes: "Colore",
  textureNotes: "Consistenza",
  usageSuggestions: "Uso consigliato",
  conservation: "Conservazione",
  targetAudience: "Target ideale",
  objections: "Obiezioni",
  faq: "FAQ",
  allowedClaims: "Claim consentiti",
  forbiddenClaims: "Claim da evitare",
  seoNotes: "Note SEO",
  adsSocialNotes: "Note Ads/Social",
  relatedProducts: "Prodotti correlati",
  priority: "Priorità",
};

type ItemFormValues = Partial<BrandProductKnowledgeItem> | Partial<BrandProductKnowledgeItemProposal>;

function renderItemFields(
  form: ItemFormValues,
  setForm: (next: ItemFormValues) => void,
  idPrefix: string,
) {
  return (
    <>
      <div className="gcr-field">
        <label htmlFor={`${idPrefix}-productName`}>Nome prodotto</label>
        <input
          id={`${idPrefix}-productName`}
          value={form.productName ?? ""}
          onChange={(e) => setForm({ ...form, productName: e.target.value })}
        />
      </div>
      <div className="gcr-field">
        <label htmlFor={`${idPrefix}-productLine`}>Linea prodotto</label>
        <input
          id={`${idPrefix}-productLine`}
          value={form.productLine ?? ""}
          onChange={(e) => setForm({ ...form, productLine: e.target.value })}
        />
      </div>
      <div className="gcr-field">
        <label htmlFor={`${idPrefix}-priority`}>Priorità commerciale</label>
        <select
          id={`${idPrefix}-priority`}
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
          ["tasteNotes", "Gusto / profumo", 2],
          ["colorNotes", "Colore", 2],
          ["textureNotes", "Consistenza", 2],
          ["usageSuggestions", "Uso consigliato", 3],
          ["conservation", "Conservazione", 2],
          ["targetAudience", "Target ideale", 2],
          ["seoNotes", "Note SEO", 3],
          ["adsSocialNotes", "Note Ads/Social", 3],
        ] as const
      ).map(([key, label, rows]) => (
        <div className="gcr-field bi-form-grid--full" key={key}>
          <label htmlFor={`${idPrefix}-${key}`}>{label}</label>
          <textarea
            id={`${idPrefix}-${key}`}
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
          ["forbiddenClaims", "Claim da evitare (uno per riga)"],
          ["relatedProducts", "Prodotti correlati (uno per riga)"],
        ] as const
      ).map(([key, label]) => (
        <div className="gcr-field bi-form-grid--full" key={key}>
          <label htmlFor={`${idPrefix}-${key}`}>{label}</label>
          <textarea
            id={`${idPrefix}-${key}`}
            rows={3}
            value={listToLines(form[key] as string[] | undefined)}
            onChange={(e) => setForm({ ...form, [key]: linesToList(e.target.value) })}
          />
        </div>
      ))}
      <div className="gcr-field bi-form-grid--full">
        <label htmlFor={`${idPrefix}-faq`}>FAQ (Domanda | Risposta, una per riga)</label>
        <textarea
          id={`${idPrefix}-faq`}
          rows={4}
          value={faqToLines(form.faq as Array<{ question: string; answer: string }> | undefined)}
          onChange={(e) => setForm({ ...form, faq: linesToFaq(e.target.value) })}
        />
      </div>
    </>
  );
}

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
            {renderItemFields(form, setForm, `item-${item.id}`)}
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

type ProposalWithKey = BrandProductKnowledgeItemProposal & { clientKey: string };

function normalizeProposalKey(value: string): string {
  return (
    value
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "product"
  );
}

function ensureProposalClientKey(
  item: BrandProductKnowledgeItemProposal,
  index: number,
): ProposalWithKey {
  const clientKey =
    item.clientKey?.trim()
    || item.shopifyProductId
    || item.suggestedShopifyProductId
    || `${normalizeProposalKey(item.productName || "product")}-${index}`;

  return { ...item, clientKey };
}

function ItemProposalAccordion({
  proposal,
  expanded,
  onToggle,
  onChange,
  onSave,
  onDiscard,
  saving,
  shopifyProducts,
  shopifyConnected,
}: {
  proposal: ProposalWithKey;
  expanded: boolean;
  onToggle: () => void;
  onChange: (next: ProposalWithKey) => void;
  onSave: () => void;
  onDiscard: () => void;
  saving: boolean;
  shopifyProducts: BrandProductKnowledgeShopifyProductOption[];
  shopifyConnected: boolean;
}) {
  const linked = Boolean(proposal.shopifyProductId ?? proposal.suggestedShopifyProductId);
  const filledFields = Object.keys(MISSING_FIELD_LABELS).filter(
    (k) => !(proposal.missingFields ?? []).includes(k),
  );

  function handleShopifyChange(productId: string) {
    if (!productId) {
      onChange({
        ...proposal,
        clientKey: proposal.clientKey,
        shopifyProductId: null,
        suggestedShopifyProductId: null,
        suggestedShopifyTitle: null,
        suggestedShopifyHandle: null,
        shopifyMatchConfidence: null,
      });
      return;
    }
    const product = shopifyProducts.find((p) => p.id === productId);
    onChange({
      ...proposal,
      clientKey: proposal.clientKey,
      shopifyProductId: productId,
      suggestedShopifyProductId: productId,
      suggestedShopifyTitle: product?.title ?? null,
      suggestedShopifyHandle: product?.handle ?? null,
      shopifyMatchConfidence: product ? 1 : null,
    });
  }

  const selectedShopifyId =
    proposal.shopifyProductId ?? proposal.suggestedShopifyProductId ?? "";

  return (
    <article className="bi-accordion gcr-card bi-pk-proposal-card">
      <header className="bi-accordion__header">
        <button type="button" className="bi-accordion__toggle" onClick={onToggle}>
          <span className="bi-accordion__title">{proposal.productName}</span>
          <span className="bi-accordion__meta">
            {proposal.productLine && <span>{proposal.productLine}</span>}
            {proposal.confidence != null && (
              <span> · Confidenza {(proposal.confidence * 100).toFixed(0)}%</span>
            )}
          </span>
          <span
            className={`bi-module-badge ${linked ? "bi-module-badge--complete" : "bi-module-badge--partial"}`}
          >
            {linked ? "Collegato a Shopify" : "Non collegato"}
          </span>
        </button>
        <div className="bi-accordion__actions">
          <button type="button" className="gcr-btn gcr-btn--sm" onClick={onToggle}>
            Modifica
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--sm gcr-btn--primary"
            disabled={saving || !proposal.productName?.trim()}
            onClick={onSave}
          >
            {saving ? "Salvataggio…" : "Salva scheda"}
          </button>
          <button type="button" className="gcr-btn gcr-btn--sm gcr-btn--ghost" onClick={onDiscard}>
            Scarta
          </button>
        </div>
      </header>
      {expanded && (
        <div className="bi-accordion__body">
          <div className="bi-pk-proposal-summary">
            {filledFields.length > 0 && (
              <p>
                <strong>Campi compilati:</strong>{" "}
                {filledFields.map((k) => MISSING_FIELD_LABELS[k] ?? k).join(", ")}
              </p>
            )}
            {(proposal.missingFields ?? []).length > 0 && (
              <p>
                <strong>Campi mancanti:</strong>{" "}
                {(proposal.missingFields ?? [])
                  .map((k) => MISSING_FIELD_LABELS[k] ?? k)
                  .join(", ")}
              </p>
            )}
            {(proposal.warnings ?? []).length > 0 && (
              <p className="bi-pk-proposal-warnings">
                <strong>Avvisi:</strong> {(proposal.warnings ?? []).join(" ")}
              </p>
            )}
          </div>
          {shopifyConnected && (
            <div className="gcr-field bi-form-grid--full">
              <label htmlFor={`proposal-shopify-${proposal.clientKey}`}>Prodotto Shopify</label>
              <select
                id={`proposal-shopify-${proposal.clientKey}`}
                value={selectedShopifyId}
                onChange={(e) => handleShopifyChange(e.target.value)}
              >
                <option value="">Nessun collegamento</option>
                {shopifyProducts.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title} (@{p.handle})
                  </option>
                ))}
              </select>
              {proposal.suggestedShopifyTitle && !proposal.shopifyProductId && (
                <p className="bi-panel__subtitle">
                  Match suggerito: {proposal.suggestedShopifyTitle}
                  {proposal.shopifyMatchConfidence != null
                    && ` (${(proposal.shopifyMatchConfidence * 100).toFixed(0)}%)`}
                </p>
              )}
            </div>
          )}
          <div className="bi-form-grid">
            {renderItemFields(
              proposal,
              (next) => onChange({ ...proposal, ...next, clientKey: proposal.clientKey }),
              `prop-${proposal.clientKey}`,
            )}
          </div>
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
  const importItemsFile = useImportProductKnowledgeItemsFromFile(projectId);
  const applyItemsProposal = useApplyProductKnowledgeItemsImportProposal(projectId);
  const createFromShopify = useCreateProductKnowledgeItemFromShopify(projectId);

  const [generalForm, setGeneralForm] = useState<Partial<BrandProductKnowledgeGeneral>>({});
  const [proposal, setProposal] = useState<BrandProductKnowledgeGeneralProposal | null>(null);
  const [importResult, setImportResult] = useState<BrandProductKnowledgeGeneralImportResponse | null>(
    null,
  );
  const [itemProposals, setItemProposals] = useState<ProposalWithKey[]>([]);
  const [itemsImportResult, setItemsImportResult] = useState<BrandProductKnowledgeItemsImportResponse | null>(
    null,
  );
  const [expandedProposalKey, setExpandedProposalKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [shopifyModalOpen, setShopifyModalOpen] = useState(false);
  const [shopifySearch, setShopifySearch] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const itemsFileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [itemsSelectedFile, setItemsSelectedFile] = useState<File | null>(null);

  const hasItemProposals = itemProposals.length > 0;
  const { data: shopifyData, isLoading: shopifyLoading } = useProductKnowledgeShopifyProducts(
    projectId,
    shopifyModalOpen || hasItemProposals,
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

  function resetItemsProposalState() {
    setItemProposals([]);
    setItemsImportResult(null);
    setItemsSelectedFile(null);
    setExpandedProposalKey(null);
    if (itemsFileInputRef.current) itemsFileInputRef.current.value = "";
  }

  function handleGenerateItemsProposal() {
    if (!itemsSelectedFile) {
      setError("Seleziona un file prima di generare le schede prodotto.");
      return;
    }
    setError(null);
    importItemsFile.mutate(itemsSelectedFile, {
      onSuccess: (res) => {
        setItemsImportResult(res);
        const normalized = res.proposal.items.map(ensureProposalClientKey);
        setItemProposals(normalized);
        if (normalized.length > 0) {
          setExpandedProposalKey(normalized[0].clientKey);
        }
      },
      onError: (err: Error) => setError(err.message),
    });
  }

  function handleSaveItemProposal(proposalToSave: ProposalWithKey) {
    setError(null);
    applyItemsProposal.mutate(
      { items: [proposalToSave] },
      {
        onSuccess: (data) => {
          if (data.saved.length > 0) {
            setSuccessMessage(data.message);
            setItemProposals((prev) => {
              const next = prev.filter((p) => p.clientKey !== proposalToSave.clientKey);
              if (next.length === 0) {
                setItemsImportResult(null);
                setItemsSelectedFile(null);
                setExpandedProposalKey(null);
                if (itemsFileInputRef.current) itemsFileInputRef.current.value = "";
              }
              return next;
            });
            if (data.saved[0]) setExpandedId(data.saved[0].id);
          }
          if (data.skipped.length > 0) {
            const skip = data.skipped[0];
            const dupMsg = skip.duplicateCandidates
              .map((d) => `${d.productName} (${d.reason})`)
              .join("; ");
            setError(`"${skip.productName}" non salvata: ${skip.reason}${dupMsg ? ` — ${dupMsg}` : ""}`);
          }
        },
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  function handleSaveAllItemProposals() {
    const valid = itemProposals.filter((p) => p.productName?.trim());
    if (valid.length === 0) {
      setError("Nessuna scheda valida da salvare.");
      return;
    }
    setError(null);
    applyItemsProposal.mutate(
      { items: valid },
      {
        onSuccess: (data) => {
          setSuccessMessage(data.message);
          if (data.skipped.length > 0) {
            const names = data.skipped.map((s) => s.productName).join(", ");
            setError(`Alcune schede saltate: ${names}. Verifica i duplicati.`);
          }
          resetItemsProposalState();
        },
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  function handleDiscardItemProposal(clientKey: string) {
    const next = itemProposals.filter((p) => p.clientKey !== clientKey);
    setItemProposals(next);
    if (next.length === 0) resetItemsProposalState();
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

        <div className="bi-pk-items-import" style={{ marginTop: "1.5rem" }}>
          <h4 className="bi-panel__title">Importa schede prodotto da file</h4>
          <p className="bi-panel__subtitle">
            Carica un file con informazioni sui prodotti. L&apos;AI creerà una proposta di schede
            prodotto specifiche compilando solo i dati presenti o chiaramente deducibili dal file.
            Potrai modificare tutto prima di salvare.
          </p>
          <div
            className="bi-dropzone"
            onClick={() => itemsFileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === "Enter" && itemsFileInputRef.current?.click()}
          >
            <p className="bi-dropzone__title">Carica file</p>
            <p className="bi-dropzone__hint">PDF, DOCX, TXT o MD — max 15 MB</p>
            {itemsSelectedFile && (
              <p>
                Selezionato: <strong>{itemsSelectedFile.name}</strong>
              </p>
            )}
            <input
              ref={itemsFileInputRef}
              type="file"
              accept={ACCEPTED_EXTENSIONS}
              style={{ display: "none" }}
              onChange={(e) => {
                setItemsSelectedFile(e.target.files?.[0] ?? null);
                setError(null);
              }}
            />
          </div>
          <div className="bi-profile-block__actions">
            <button
              type="button"
              className="gcr-btn gcr-btn--primary"
              disabled={importItemsFile.isPending || !itemsSelectedFile}
              onClick={handleGenerateItemsProposal}
            >
              {importItemsFile.isPending ? "Generazione…" : "Genera schede prodotto"}
            </button>
          </div>
        </div>

        {itemProposals.length > 0 && (
          <section className="bi-pk-proposals-section" style={{ marginTop: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
              <div>
                <h4 className="bi-panel__title">Proposta schede prodotto</h4>
                {itemsImportResult && (
                  <p className="bi-panel__subtitle">
                    {itemsImportResult.sourceSummary && (
                      <>Anteprima: {itemsImportResult.sourceSummary.slice(0, 120)}… </>
                    )}
                    {itemsImportResult.warnings.length > 0 && itemsImportResult.warnings.join(" ")}
                  </p>
                )}
              </div>
              <div className="bi-profile-block__actions" style={{ margin: 0 }}>
                <button
                  type="button"
                  className="gcr-btn gcr-btn--primary"
                  disabled={applyItemsProposal.isPending}
                  onClick={handleSaveAllItemProposals}
                >
                  {applyItemsProposal.isPending ? "Salvataggio…" : "Salva tutte le schede valide"}
                </button>
                <button
                  type="button"
                  className="gcr-btn gcr-btn--ghost"
                  onClick={resetItemsProposalState}
                >
                  Scarta proposta
                </button>
              </div>
            </div>
            <div className="bi-accordion-list" style={{ marginTop: "1rem" }}>
              {itemProposals.map((itemProposal) => (
                <ItemProposalAccordion
                  key={itemProposal.clientKey}
                  proposal={itemProposal}
                  expanded={expandedProposalKey === itemProposal.clientKey}
                  onToggle={() =>
                    setExpandedProposalKey(
                      expandedProposalKey === itemProposal.clientKey
                        ? null
                        : itemProposal.clientKey,
                    )
                  }
                  onChange={(next) =>
                    setItemProposals((prev) =>
                      prev.map((p) => (p.clientKey === next.clientKey ? next : p)),
                    )
                  }
                  onSave={() => handleSaveItemProposal(itemProposal)}
                  onDiscard={() => handleDiscardItemProposal(itemProposal.clientKey)}
                  saving={applyItemsProposal.isPending}
                  shopifyProducts={shopifyData?.products ?? []}
                  shopifyConnected={shopifyData?.shopifyConnected ?? false}
                />
              ))}
            </div>
          </section>
        )}

        {itemsLoading && <p className="bi-panel__subtitle">Caricamento schede…</p>}
        {!itemsLoading && items.length === 0 && !hasItemProposals && (
          <p className="bi-panel__subtitle" style={{ marginTop: "1rem" }}>
            Nessuna scheda prodotto. Aggiungi un prodotto da Shopify o importa schede da file.
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
