import { FormEvent, useEffect, useRef, useState } from "react";
import type {
  BrandFaqObjections,
  BrandFaqObjectionsImportResponse,
  BrandFaqObjectionsProposal,
} from "@gcr/shared";
import {
  useApplyFaqObjectionsProposal,
  useFaqObjections,
  useImportFaqObjectionsFromFile,
  useUpdateFaqObjections,
} from "../../hooks/useBrandIntelligence";

interface BrandFaqObjectionsPanelProps {
  projectId: string;
}

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.txt,.md";

const NORMALIZE_ERROR_MESSAGE =
  "Il file è stato letto, ma la proposta non è stata normalizzata correttamente. Riprova o usa un file più strutturato.";

const OFFICIAL_LIST_FIELDS = [
  ["generalFaq", "FAQ generali (una voce per riga, es. Domanda: ... / Risposta: ...)"],
  ["productProcessQuestions", "Domande prodotto/processo (una voce per riga)"],
  ["purchaseShippingQuestions", "Domande acquisto/spedizione (una voce per riga)"],
  ["objections", "Obiezioni frequenti (uno per riga)"],
  ["mythsMisconceptions", "Falsi miti / fraintendimenti (uno per riga)"],
  ["recommendedAnswers", "Risposte consigliate (uno per riga)"],
  ["contentOpportunities", "Opportunità contenuto (uno per riga)"],
  ["socialCommentInsights", "Insight commenti social (uno per riga)"],
] as const;

type OfficialListFieldKey = (typeof OFFICIAL_LIST_FIELDS)[number][0];

function linesToList(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function listToLines(list: string[] | null | undefined): string {
  return (list ?? []).join("\n");
}

function coerceLegacyItem(item: unknown): string | null {
  if (typeof item === "string") {
    const trimmed = item.trim();
    return trimmed || null;
  }
  if (!item || typeof item !== "object") {
    return null;
  }
  const record = item as Record<string, unknown>;
  const question = [record.question, record.domanda].find((v) => typeof v === "string") as
    | string
    | undefined;
  const answer = [record.answer, record.risposta, record.response].find(
    (v) => typeof v === "string",
  ) as string | undefined;
  if (question?.trim()) {
    const q = question.trim();
    const a = answer?.trim() ?? "";
    return a ? `Domanda: ${q}\nRisposta: ${a}` : `Domanda: ${q}`;
  }
  const objection = [record.objection, record.obiezione].find((v) => typeof v === "string") as
    | string
    | undefined;
  const objectionAnswer = [record.answer, record.risposta].find((v) => typeof v === "string") as
    | string
    | undefined;
  if (objection?.trim()) {
    const o = objection.trim();
    const a = objectionAnswer?.trim() ?? "";
    return a ? `Obiezione: ${o}\nRisposta consigliata: ${a}` : o;
  }
  const myth = [record.myth, record.mito].find((v) => typeof v === "string") as string | undefined;
  const correction = [record.correction, record.correzione].find((v) => typeof v === "string") as
    | string
    | undefined;
  if (myth?.trim()) {
    const m = myth.trim();
    const c = correction?.trim() ?? "";
    return c ? `Mito: ${m}\nCorrezione: ${c}` : `Mito: ${m}`;
  }
  const insight = typeof record.insight === "string" ? record.insight.trim() : "";
  const doubt = [record.doubt, record.dubbio].find((v) => typeof v === "string") as
    | string
    | undefined;
  const reply = [record.suggestedReply, record.suggested_reply, record.reply].find(
    (v) => typeof v === "string",
  ) as string | undefined;
  if (insight || doubt?.trim() || reply?.trim()) {
    const parts: string[] = [];
    if (insight) parts.push(`Insight: ${insight}`);
    if (doubt?.trim()) parts.push(`Dubbio: ${doubt.trim()}`);
    if (reply?.trim()) parts.push(`Risposta: ${reply.trim()}`);
    return parts.join(" | ");
  }
  const text = [record.text, record.testo, record.content].find((v) => typeof v === "string") as
    | string
    | undefined;
  if (text?.trim()) return text.trim();
  const value = [record.value, record.valore].find((v) => typeof v === "string") as
    | string
    | undefined;
  if (value?.trim()) return value.trim();
  return null;
}

function coerceStringList(value: unknown): string[] {
  if (!value) return [];
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed ? [trimmed] : [];
  }
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  const out: string[] = [];
  for (const item of value) {
    const text = coerceLegacyItem(item);
    if (text && !seen.has(text)) {
      seen.add(text);
      out.push(text);
    }
  }
  return out;
}

type OfficialFormState = Partial<BrandFaqObjections>;
type ProposalFormState = Partial<BrandFaqObjectionsProposal>;

function rowToOfficialForm(row: BrandFaqObjections): OfficialFormState {
  return {
    generalFaq: coerceStringList(row.generalFaq),
    productProcessQuestions: coerceStringList(row.productProcessQuestions),
    purchaseShippingQuestions: coerceStringList(row.purchaseShippingQuestions),
    objections: coerceStringList(row.objections),
    mythsMisconceptions: coerceStringList(row.mythsMisconceptions),
    recommendedAnswers: coerceStringList(row.recommendedAnswers),
    contentOpportunities: coerceStringList(row.contentOpportunities),
    socialCommentInsights: coerceStringList(row.socialCommentInsights),
    notes: row.notes ?? "",
  };
}

function proposalToForm(proposal: BrandFaqObjectionsProposal): ProposalFormState {
  return {
    generalFaq: proposal.generalFaq ?? [],
    productProcessQuestions: proposal.productProcessQuestions ?? [],
    purchaseShippingQuestions: proposal.purchaseShippingQuestions ?? [],
    objections: proposal.objections ?? [],
    mythsMisconceptions: proposal.mythsMisconceptions ?? [],
    recommendedAnswers: proposal.recommendedAnswers ?? [],
    contentOpportunities: proposal.contentOpportunities ?? [],
    socialCommentInsights: proposal.socialCommentInsights ?? [],
    notes: proposal.notes ?? "",
  };
}

function formToProposal(form: ProposalFormState): BrandFaqObjectionsProposal {
  return {
    generalFaq: form.generalFaq?.length ? form.generalFaq : undefined,
    productProcessQuestions: form.productProcessQuestions?.length
      ? form.productProcessQuestions
      : undefined,
    purchaseShippingQuestions: form.purchaseShippingQuestions?.length
      ? form.purchaseShippingQuestions
      : undefined,
    objections: form.objections?.length ? form.objections : undefined,
    mythsMisconceptions: form.mythsMisconceptions?.length ? form.mythsMisconceptions : undefined,
    recommendedAnswers: form.recommendedAnswers?.length ? form.recommendedAnswers : undefined,
    contentOpportunities: form.contentOpportunities?.length
      ? form.contentOpportunities
      : undefined,
    socialCommentInsights: form.socialCommentInsights?.length
      ? form.socialCommentInsights
      : undefined,
    notes: form.notes || undefined,
  };
}

function officialFormToUpdate(form: OfficialFormState) {
  return {
    generalFaq: form.generalFaq?.length ? form.generalFaq : undefined,
    productProcessQuestions: form.productProcessQuestions?.length
      ? form.productProcessQuestions
      : undefined,
    purchaseShippingQuestions: form.purchaseShippingQuestions?.length
      ? form.purchaseShippingQuestions
      : undefined,
    objections: form.objections?.length ? form.objections : undefined,
    mythsMisconceptions: form.mythsMisconceptions?.length ? form.mythsMisconceptions : undefined,
    recommendedAnswers: form.recommendedAnswers?.length ? form.recommendedAnswers : undefined,
    contentOpportunities: form.contentOpportunities?.length
      ? form.contentOpportunities
      : undefined,
    socialCommentInsights: form.socialCommentInsights?.length
      ? form.socialCommentInsights
      : undefined,
    notes: form.notes || undefined,
  };
}

function proposalHasData(proposal: BrandFaqObjectionsProposal): boolean {
  return Boolean(
    (proposal.generalFaq?.length ?? 0) > 0
      || (proposal.objections?.length ?? 0) > 0
      || (proposal.recommendedAnswers?.length ?? 0) > 0
      || (proposal.productProcessQuestions?.length ?? 0) > 0,
  );
}

function rowHasData(row: BrandFaqObjections): boolean {
  return Boolean(
    (row.generalFaq?.length ?? 0) > 0
      || (row.objections?.length ?? 0) > 0
      || (row.recommendedAnswers?.length ?? 0) > 0,
  );
}

function mapImportError(message: string): string {
  if (
    message.includes("Impossibile normalizzare la proposta FAQ")
    || message.includes("normalizzata correttamente")
  ) {
    return NORMALIZE_ERROR_MESSAGE;
  }
  return message;
}

function renderListFields<T extends OfficialFormState | ProposalFormState>(
  fields: readonly (readonly [string, string])[],
  values: T,
  onChange: (next: T) => void,
  idPrefix: string,
) {
  return (
    <div className="bi-form-grid">
      {fields.map(([key, label]) => (
        <div className="gcr-field bi-form-grid--full" key={key}>
          <label htmlFor={`${idPrefix}-${key}`}>{label}</label>
          <textarea
            id={`${idPrefix}-${key}`}
            rows={key === "socialCommentInsights" ? 3 : 4}
            value={listToLines(values[key as OfficialListFieldKey] as string[] | undefined)}
            onChange={(e) =>
              onChange({ ...values, [key]: linesToList(e.target.value) })
            }
          />
        </div>
      ))}
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

export function BrandFaqObjectionsPanel({ projectId }: BrandFaqObjectionsPanelProps) {
  const { data: faqObjections, isLoading } = useFaqObjections(projectId);
  const update = useUpdateFaqObjections(projectId);
  const importFile = useImportFaqObjectionsFromFile(projectId);
  const applyProposal = useApplyFaqObjectionsProposal(projectId);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<BrandFaqObjectionsImportResponse | null>(
    null,
  );
  const [proposal, setProposal] = useState<BrandFaqObjectionsProposal | null>(null);
  const [officialForm, setOfficialForm] = useState<OfficialFormState>({});
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!faqObjections) return;
    setOfficialForm(rowToOfficialForm(faqObjections));
  }, [faqObjections]);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSelectedFile(e.target.files?.[0] ?? null);
    setError(null);
  }

  function handleGenerateProposal() {
    if (!selectedFile) {
      setError("Seleziona un file prima di generare la proposta.");
      return;
    }
    setError(null);
    setSuccessMessage(null);
    importFile.mutate(selectedFile, {
      onSuccess: (res) => {
        setImportResult(res);
        setProposal({ ...res.proposal });
      },
      onError: (err: Error) => setError(mapImportError(err.message)),
    });
  }

  function handleCancelProposal() {
    setProposal(null);
    setImportResult(null);
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function handleApplyProposal() {
    if (!proposal) return;
    setError(null);
    setSuccessMessage(null);
    const hadData = proposalHasData(proposal);
    applyProposal.mutate(
      { proposal },
      {
        onSuccess: (data) => {
          if (hadData && !rowHasData(data.faqObjections)) {
            setError("La proposta non è stata salvata correttamente. Riprova.");
            return;
          }
          setOfficialForm(rowToOfficialForm(data.faqObjections));
          setSuccessMessage(data.message || "FAQ & Objections aggiornati.");
          handleCancelProposal();
        },
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  function handleSave(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    update.mutate(officialFormToUpdate(officialForm), {
      onSuccess: () => setSuccessMessage("FAQ & Objections salvati."),
      onError: (err: Error) => setError(err.message),
    });
  }

  if (isLoading) return <p className="bi-panel__subtitle">Caricamento…</p>;

  return (
    <div className="bi-profile-v1">
      {error && (
        <div className="gcr-alert gcr-alert--error" style={{ marginBottom: "1rem" }}>
          {error}
        </div>
      )}
      {successMessage && (
        <div className="gcr-alert gcr-alert--success" style={{ marginBottom: "1rem" }}>
          {successMessage}
        </div>
      )}

      <section className="bi-profile-block gcr-card">
        <h3 className="bi-panel__title">Importa da file</h3>
        <p className="bi-panel__subtitle">
          Carica un documento con FAQ, obiezioni, commenti social o dubbi clienti. L&apos;AI
          estrarrà solo informazioni utili a questa sezione. Potrai modificare tutto prima di
          salvare.
        </p>
        <div
          className="bi-dropzone"
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={(e) => e.key === "Enter" && fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
        >
          <p className="bi-dropzone__title">Carica file</p>
          <p className="bi-dropzone__hint">PDF, DOCX, TXT o MD — max 15 MB, 1 file per volta</p>
          {selectedFile && (
            <p className="bi-panel__subtitle" style={{ margin: 0 }}>
              Selezionato: <strong>{selectedFile.name}</strong>
            </p>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_EXTENSIONS}
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
        </div>
        <div className="bi-profile-block__actions">
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={importFile.isPending || !selectedFile}
            onClick={handleGenerateProposal}
          >
            {importFile.isPending ? "Generazione…" : "Genera proposta FAQ"}
          </button>
        </div>
      </section>

      {proposal && (
        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Proposta AI</h3>
          {importResult && (
            <p className="bi-panel__subtitle">
              Confidenza: {(importResult.confidence * 100).toFixed(0)}%
              {importResult.warnings.length > 0 && (
                <> — {importResult.warnings.join(" ")}</>
              )}
            </p>
          )}
          {renderListFields(
            OFFICIAL_LIST_FIELDS,
            proposalToForm(proposal),
            (next) => setProposal(formToProposal(next)),
            "proposal",
          )}
          <div className="bi-profile-block__actions">
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary"
              disabled={importFile.isPending}
              onClick={handleGenerateProposal}
            >
              Rigenera
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary"
              onClick={handleCancelProposal}
            >
              Annulla
            </button>
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
        <h3 className="bi-panel__title">FAQ &amp; Objections ufficiali</h3>
        <p className="bi-panel__subtitle">
          Domande frequenti, obiezioni e risposte consigliate usate dai moduli AI (Product SEO,
          Content SEO, PED, blog, social).
        </p>
        <form onSubmit={handleSave}>
          {renderListFields(OFFICIAL_LIST_FIELDS, officialForm, setOfficialForm, "official")}
          <div className="bi-profile-block__actions">
            <button
              type="submit"
              className="gcr-btn gcr-btn--primary"
              disabled={update.isPending}
            >
              {update.isPending ? "Salvataggio…" : "Salva FAQ & Objections"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
