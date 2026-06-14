import { FormEvent, useEffect, useRef, useState } from "react";
import type {
  BrandFaqObjections,
  BrandFaqObjectionsImportResponse,
  BrandFaqObjectionsProposal,
  FaqEntry,
  SocialCommentInsight,
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

const LIST_FIELDS = [
  ["objections", "Obiezioni frequenti (uno per riga)"],
  ["mythsMisconceptions", "Falsi miti / fraintendimenti (uno per riga)"],
  ["recommendedAnswers", "Risposte consigliate (uno per riga)"],
  ["contentOpportunities", "Opportunità contenuto (uno per riga)"],
] as const;

const FAQ_FIELDS = [
  ["generalFaq", "FAQ generali (Domanda | Risposta, una per riga)"],
  ["productProcessQuestions", "Domande prodotto/processo (Domanda | Risposta)"],
  ["purchaseShippingQuestions", "Domande acquisto/spedizione (Domanda | Risposta)"],
] as const;

type ListFieldKey = (typeof LIST_FIELDS)[number][0];
type FaqFieldKey = (typeof FAQ_FIELDS)[number][0];

function linesToList(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function listToLines(list: string[] | null | undefined): string {
  return (list ?? []).join("\n");
}

function faqToLines(faq: FaqEntry[] | null | undefined): string {
  return (faq ?? [])
    .map((e) => `${e.question}${e.answer ? ` | ${e.answer}` : ""}`)
    .join("\n");
}

function linesToFaq(text: string): FaqEntry[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [question, ...rest] = line.split("|");
      return {
        question: (question ?? "").trim(),
        answer: rest.join("|").trim(),
      };
    })
    .filter((e) => e.question);
}

function socialToLines(insights: SocialCommentInsight[] | null | undefined): string {
  return (insights ?? [])
    .map((s) => {
      const parts = [s.insight, s.doubt, s.suggestedReply ?? ""].filter(Boolean);
      return parts.join(" | ");
    })
    .join("\n");
}

function linesToSocial(text: string): SocialCommentInsight[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [insight, doubt, suggestedReply] = line.split("|").map((p) => p.trim());
      return {
        insight: insight ?? "",
        doubt: doubt ?? "",
        suggestedReply: suggestedReply || null,
      };
    })
    .filter((s) => s.insight || s.doubt);
}

type FormState = Partial<BrandFaqObjections>;

function rowToForm(row: BrandFaqObjections): FormState {
  return {
    generalFaq: row.generalFaq ?? [],
    productProcessQuestions: row.productProcessQuestions ?? [],
    purchaseShippingQuestions: row.purchaseShippingQuestions ?? [],
    objections: row.objections ?? [],
    mythsMisconceptions: row.mythsMisconceptions ?? [],
    recommendedAnswers: row.recommendedAnswers ?? [],
    contentOpportunities: row.contentOpportunities ?? [],
    socialCommentInsights: row.socialCommentInsights ?? [],
    notes: row.notes ?? "",
  };
}

function proposalToForm(proposal: BrandFaqObjectionsProposal): FormState {
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

function formToProposal(form: FormState): BrandFaqObjectionsProposal {
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
  const [form, setForm] = useState<FormState>({});
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!faqObjections) return;
    setForm(rowToForm(faqObjections));
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
      onError: (err: Error) => setError(err.message),
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
          setForm(rowToForm(data.faqObjections));
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
    const payload = formToProposal(form);
    update.mutate(payload, {
      onSuccess: () => setSuccessMessage("FAQ & Objections salvati."),
      onError: (err: Error) => setError(err.message),
    });
  }

  function renderFields(
    values: FormState,
    onChange: (next: FormState) => void,
    idPrefix: string,
  ) {
    return (
      <div className="bi-form-grid">
        {FAQ_FIELDS.map(([key, label]) => (
          <div className="gcr-field bi-form-grid--full" key={key}>
            <label htmlFor={`${idPrefix}-${key}`}>{label}</label>
            <textarea
              id={`${idPrefix}-${key}`}
              rows={4}
              value={faqToLines(values[key as FaqFieldKey] as FaqEntry[] | undefined)}
              onChange={(e) =>
                onChange({ ...values, [key]: linesToFaq(e.target.value) })
              }
            />
          </div>
        ))}
        {LIST_FIELDS.map(([key, label]) => (
          <div className="gcr-field bi-form-grid--full" key={key}>
            <label htmlFor={`${idPrefix}-${key}`}>{label}</label>
            <textarea
              id={`${idPrefix}-${key}`}
              rows={3}
              value={listToLines(values[key as ListFieldKey] as string[] | undefined)}
              onChange={(e) =>
                onChange({ ...values, [key]: linesToList(e.target.value) })
              }
            />
          </div>
        ))}
        <div className="gcr-field bi-form-grid--full">
          <label htmlFor={`${idPrefix}-socialCommentInsights`}>
            Insight commenti social (insight | dubbio | risposta opzionale)
          </label>
          <textarea
            id={`${idPrefix}-socialCommentInsights`}
            rows={3}
            value={socialToLines(values.socialCommentInsights)}
            onChange={(e) =>
              onChange({ ...values, socialCommentInsights: linesToSocial(e.target.value) })
            }
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
          {renderFields(proposalToForm(proposal), (next) => {
            setProposal(formToProposal(next));
          }, "proposal")}
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
          {renderFields(form, setForm, "official")}
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
