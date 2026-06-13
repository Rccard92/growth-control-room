import { FormEvent, useEffect, useRef, useState } from "react";
import type {
  BrandSafeClaims,
  BrandSafeClaimsImportResponse,
  BrandSafeClaimsProposal,
} from "@gcr/shared";
import {
  useApplyBrandSafeClaimsProposal,
  useBrandSafeClaims,
  useImportBrandSafeClaimsFromFile,
  useUpdateBrandSafeClaims,
} from "../../hooks/useBrandIntelligence";

interface BrandSafeClaimsPanelProps {
  projectId: string;
}

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.txt,.md";

const LIST_FIELDS = [
  ["allowedClaims", "Claim consentiti (uno per riga)"],
  ["forbiddenClaims", "Claim vietati (uno per riga)"],
  ["cautionClaims", "Claim da usare con cautela (uno per riga)"],
  ["disclaimers", "Disclaimer (uno per riga)"],
  ["healthClaimRules", "Regole claim salutistici (uno per riga)"],
  ["competitorRules", "Regole competitor (uno per riga)"],
  ["processSecrets", "Process secrets — non divulgare (uno per riga)"],
  ["toneRedFlags", "Tone red flags (uno per riga)"],
] as const;

type ListFieldKey = (typeof LIST_FIELDS)[number][0];

function linesToList(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function listToLines(list: string[] | null | undefined): string {
  return (list ?? []).join("\n");
}

function safeClaimsToForm(row: BrandSafeClaims): Partial<BrandSafeClaims> {
  return {
    allowedClaims: row.allowedClaims ?? [],
    forbiddenClaims: row.forbiddenClaims ?? [],
    cautionClaims: row.cautionClaims ?? [],
    disclaimers: row.disclaimers ?? [],
    healthClaimRules: row.healthClaimRules ?? [],
    competitorRules: row.competitorRules ?? [],
    processSecrets: row.processSecrets ?? [],
    toneRedFlags: row.toneRedFlags ?? [],
    notes: row.notes ?? "",
  };
}

function proposalToForm(proposal: BrandSafeClaimsProposal): Partial<BrandSafeClaims> {
  return {
    allowedClaims: proposal.allowedClaims ?? [],
    forbiddenClaims: proposal.forbiddenClaims ?? [],
    cautionClaims: proposal.cautionClaims ?? [],
    disclaimers: proposal.disclaimers ?? [],
    healthClaimRules: proposal.healthClaimRules ?? [],
    competitorRules: proposal.competitorRules ?? [],
    processSecrets: proposal.processSecrets ?? [],
    toneRedFlags: proposal.toneRedFlags ?? [],
    notes: proposal.notes ?? "",
  };
}

function proposalHasData(proposal: BrandSafeClaimsProposal): boolean {
  return Boolean(
    (proposal.allowedClaims?.length ?? 0) > 0
      || (proposal.forbiddenClaims?.length ?? 0) > 0
      || (proposal.cautionClaims?.length ?? 0) > 0
      || (proposal.disclaimers?.length ?? 0) > 0,
  );
}

function safeClaimsHasData(row: BrandSafeClaims): boolean {
  return Boolean(
    (row.allowedClaims?.length ?? 0) > 0 || (row.forbiddenClaims?.length ?? 0) > 0,
  );
}

export function BrandSafeClaimsPanel({ projectId }: BrandSafeClaimsPanelProps) {
  const { data: safeClaims, isLoading } = useBrandSafeClaims(projectId);
  const update = useUpdateBrandSafeClaims(projectId);
  const importFile = useImportBrandSafeClaimsFromFile(projectId);
  const applyProposal = useApplyBrandSafeClaimsProposal(projectId);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<BrandSafeClaimsImportResponse | null>(null);
  const [proposal, setProposal] = useState<BrandSafeClaimsProposal | null>(null);
  const [form, setForm] = useState<Partial<BrandSafeClaims>>({});
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!safeClaims) return;
    setForm(safeClaimsToForm(safeClaims));
  }, [safeClaims]);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
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

  function handleApplyProposal() {
    if (!proposal) return;
    setError(null);
    setSuccessMessage(null);
    const hadData = proposalHasData(proposal);
    applyProposal.mutate(
      { proposal },
      {
        onSuccess: (data) => {
          if (hadData && !safeClaimsHasData(data.safeClaims)) {
            setError("La proposta non è stata salvata correttamente. Riprova.");
            return;
          }
          setForm(safeClaimsToForm(data.safeClaims));
          setSuccessMessage(data.message || "Safe Claims aggiornati.");
          setProposal(null);
          setImportResult(null);
          setSelectedFile(null);
          if (fileInputRef.current) fileInputRef.current.value = "";
        },
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  function handleSave(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    update.mutate(
      {
        allowedClaims: form.allowedClaims?.length ? form.allowedClaims : undefined,
        forbiddenClaims: form.forbiddenClaims?.length ? form.forbiddenClaims : undefined,
        cautionClaims: form.cautionClaims?.length ? form.cautionClaims : undefined,
        disclaimers: form.disclaimers?.length ? form.disclaimers : undefined,
        healthClaimRules: form.healthClaimRules?.length ? form.healthClaimRules : undefined,
        competitorRules: form.competitorRules?.length ? form.competitorRules : undefined,
        processSecrets: form.processSecrets?.length ? form.processSecrets : undefined,
        toneRedFlags: form.toneRedFlags?.length ? form.toneRedFlags : undefined,
        notes: form.notes || undefined,
      },
      {
        onSuccess: () => setSuccessMessage("Safe Claims salvati."),
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  function renderFields(
    values: Partial<BrandSafeClaims>,
    onChange: (next: Partial<BrandSafeClaims>) => void,
    idPrefix: string,
  ) {
    return (
      <div className="bi-form-grid">
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
          <label htmlFor={`${idPrefix}-notes`}>Note</label>
          <textarea
            id={`${idPrefix}-notes`}
            rows={4}
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
        <h3 className="bi-panel__title">Importa Safe Claims da file</h3>
        <p className="bi-panel__subtitle">
          Carica un documento con policy, claim consentiti/vietati e red flags. L&apos;AI estrarrà
          solo informazioni relative a Safe Claims. Potrai modificare tutto prima di salvare.
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
              {importResult.warnings.length > 0 && (
                <> — {importResult.warnings.join(" ")}</>
              )}
            </p>
          )}
          {renderFields(proposalToForm(proposal), (next) => {
            setProposal({
              allowedClaims: next.allowedClaims,
              forbiddenClaims: next.forbiddenClaims,
              cautionClaims: next.cautionClaims,
              disclaimers: next.disclaimers,
              healthClaimRules: next.healthClaimRules,
              competitorRules: next.competitorRules,
              processSecrets: next.processSecrets,
              toneRedFlags: next.toneRedFlags,
              notes: next.notes,
            });
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
        <h3 className="bi-panel__title">Safe Claims ufficiali</h3>
        <p className="bi-panel__subtitle">
          Definisci claim consentiti, vietati e red flags usati dai moduli AI (Product SEO, Content
          SEO, ecc.).
        </p>
        <form onSubmit={handleSave}>
          {renderFields(form, setForm, "official")}
          <div className="bi-profile-block__actions">
            <button
              type="submit"
              className="gcr-btn gcr-btn--primary"
              disabled={update.isPending}
            >
              {update.isPending ? "Salvataggio…" : "Salva Safe Claims"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
