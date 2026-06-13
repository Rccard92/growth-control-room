import { FormEvent, useEffect, useRef, useState } from "react";
import type { BrandIdentity, BrandIdentityImportResponse, BrandIdentityProposal } from "@gcr/shared";
import {
  useApplyBrandIdentityProposal,
  useBrandIdentity,
  useImportBrandIdentityFromFile,
  useUpdateBrandIdentity,
} from "../../hooks/useBrandIntelligence";

interface BrandIdentityPanelProps {
  projectId: string;
}

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.txt,.md";

function linesToList(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function listToLines(list: string[] | null | undefined): string {
  return (list ?? []).join("\n");
}

function identityToForm(identity: BrandIdentity): Partial<BrandIdentity> {
  return {
    positioning: identity.positioning ?? "",
    brandValues: identity.brandValues ?? [],
    differentiators: identity.differentiators ?? [],
    productionPrinciples: identity.productionPrinciples ?? [],
    qualityPrinciples: identity.qualityPrinciples ?? [],
    trustElements: identity.trustElements ?? [],
    whatBrandIs: identity.whatBrandIs ?? "",
    whatBrandIsNot: identity.whatBrandIsNot ?? "",
    storytellingNotes: identity.storytellingNotes ?? "",
  };
}

function proposalToForm(proposal: BrandIdentityProposal): Partial<BrandIdentity> {
  return {
    positioning: proposal.positioning ?? "",
    brandValues: proposal.brandValues ?? [],
    differentiators: proposal.differentiators ?? [],
    productionPrinciples: proposal.productionPrinciples ?? [],
    qualityPrinciples: proposal.qualityPrinciples ?? [],
    trustElements: proposal.trustElements ?? [],
    whatBrandIs: proposal.whatBrandIs ?? "",
    whatBrandIsNot: proposal.whatBrandIsNot ?? "",
    storytellingNotes: proposal.storytellingNotes ?? "",
  };
}

function proposalHasData(proposal: BrandIdentityProposal): boolean {
  return Boolean(
    proposal.positioning?.trim()
      || (proposal.brandValues?.length ?? 0) > 0
      || (proposal.differentiators?.length ?? 0) > 0
      || proposal.whatBrandIs?.trim()
      || proposal.storytellingNotes?.trim(),
  );
}

function identityHasData(identity: BrandIdentity): boolean {
  return Boolean(
    identity.positioning?.trim()
      || (identity.brandValues?.length ?? 0) > 0
      || identity.whatBrandIs?.trim(),
  );
}

export function BrandIdentityPanel({ projectId }: BrandIdentityPanelProps) {
  const { data: identity, isLoading } = useBrandIdentity(projectId);
  const update = useUpdateBrandIdentity(projectId);
  const importFile = useImportBrandIdentityFromFile(projectId);
  const applyProposal = useApplyBrandIdentityProposal(projectId);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<BrandIdentityImportResponse | null>(null);
  const [proposal, setProposal] = useState<BrandIdentityProposal | null>(null);
  const [form, setForm] = useState<Partial<BrandIdentity>>({});
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!identity) return;
    setForm(identityToForm(identity));
  }, [identity]);

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

  function handleRegenerate() {
    handleGenerateProposal();
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
          if (hadData && !identityHasData(data.brandIdentity)) {
            setError("La proposta non è stata salvata correttamente. Riprova.");
            return;
          }
          setForm(identityToForm(data.brandIdentity));
          setSuccessMessage(data.message || "Brand Identity aggiornata.");
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
        positioning: form.positioning || undefined,
        brandValues: form.brandValues?.length ? form.brandValues : undefined,
        differentiators: form.differentiators?.length ? form.differentiators : undefined,
        productionPrinciples: form.productionPrinciples?.length
          ? form.productionPrinciples
          : undefined,
        qualityPrinciples: form.qualityPrinciples?.length ? form.qualityPrinciples : undefined,
        trustElements: form.trustElements?.length ? form.trustElements : undefined,
        whatBrandIs: form.whatBrandIs || undefined,
        whatBrandIsNot: form.whatBrandIsNot || undefined,
        storytellingNotes: form.storytellingNotes || undefined,
      },
      {
        onSuccess: () => setSuccessMessage("Brand Identity salvata."),
        onError: (err: Error) => setError(err.message),
      },
    );
  }

  function renderIdentityFields(
    values: Partial<BrandIdentity>,
    onChange: (next: Partial<BrandIdentity>) => void,
    idPrefix: string,
  ) {
    return (
      <div className="bi-form-grid">
        <div className="gcr-field bi-form-grid--full">
          <label htmlFor={`${idPrefix}-positioning`}>Posizionamento</label>
          <textarea
            id={`${idPrefix}-positioning`}
            rows={3}
            value={values.positioning ?? ""}
            onChange={(e) => onChange({ ...values, positioning: e.target.value })}
          />
        </div>

        {(
          [
            ["brandValues", "Valori del brand (uno per riga)"],
            ["differentiators", "Differenziatori (uno per riga)"],
            ["productionPrinciples", "Principi produttivi (uno per riga)"],
            ["qualityPrinciples", "Principi di qualità (uno per riga)"],
            ["trustElements", "Elementi di fiducia (uno per riga)"],
          ] as const
        ).map(([key, label]) => (
          <div className="gcr-field bi-form-grid--full" key={key}>
            <label htmlFor={`${idPrefix}-${key}`}>{label}</label>
            <textarea
              id={`${idPrefix}-${key}`}
              rows={3}
              value={listToLines(values[key] as string[] | undefined)}
              onChange={(e) =>
                onChange({ ...values, [key]: linesToList(e.target.value) })
              }
            />
          </div>
        ))}

        <div className="gcr-field bi-form-grid--full">
          <label htmlFor={`${idPrefix}-whatBrandIs`}>Cosa il brand è</label>
          <textarea
            id={`${idPrefix}-whatBrandIs`}
            rows={3}
            value={values.whatBrandIs ?? ""}
            onChange={(e) => onChange({ ...values, whatBrandIs: e.target.value })}
          />
        </div>

        <div className="gcr-field bi-form-grid--full">
          <label htmlFor={`${idPrefix}-whatBrandIsNot`}>Cosa il brand non è</label>
          <textarea
            id={`${idPrefix}-whatBrandIsNot`}
            rows={3}
            value={values.whatBrandIsNot ?? ""}
            onChange={(e) => onChange({ ...values, whatBrandIsNot: e.target.value })}
          />
        </div>

        <div className="gcr-field bi-form-grid--full">
          <label htmlFor={`${idPrefix}-storytellingNotes`}>Note storytelling</label>
          <textarea
            id={`${idPrefix}-storytellingNotes`}
            rows={4}
            value={values.storytellingNotes ?? ""}
            onChange={(e) => onChange({ ...values, storytellingNotes: e.target.value })}
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
        <h3 className="bi-panel__title">Importa Brand Identity da file</h3>
        <p className="bi-panel__subtitle">
          Carica un solo file dedicato all&apos;identità del brand. L&apos;AI estrarrà solo
          posizionamento, valori, differenziatori, principi e note storytelling. Potrai modificare
          tutto prima di salvare.
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
        <div className="bi-profile-actions">
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={importFile.isPending || !selectedFile}
            onClick={handleGenerateProposal}
          >
            {importFile.isPending ? "Generazione in corso…" : "Genera proposta Brand Identity"}
          </button>
        </div>
      </section>

      {proposal && (
        <section className="bi-profile-block gcr-card bi-visual-proposal">
          <h3 className="bi-panel__title">Proposta AI Brand Identity</h3>
          {importResult && (
            <p className="bi-source-confidence">
              Confidence: {Math.round(importResult.confidence * 100)}%
            </p>
          )}
          {importResult?.warnings.length ? (
            <ul className="bi-warnings-list">
              {importResult.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          ) : null}
          {renderIdentityFields(proposalToForm(proposal), (next) => {
            setProposal({
              positioning: next.positioning,
              brandValues: next.brandValues,
              differentiators: next.differentiators,
              productionPrinciples: next.productionPrinciples,
              qualityPrinciples: next.qualityPrinciples,
              trustElements: next.trustElements,
              whatBrandIs: next.whatBrandIs,
              whatBrandIsNot: next.whatBrandIsNot,
              storytellingNotes: next.storytellingNotes,
            });
          }, "proposal")}
          <div className="bi-profile-actions">
            <button
              type="button"
              className="gcr-btn gcr-btn--primary"
              disabled={applyProposal.isPending}
              onClick={handleApplyProposal}
            >
              {applyProposal.isPending ? "Applicazione…" : "Applica proposta"}
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost"
              disabled={importFile.isPending || !selectedFile}
              onClick={handleRegenerate}
            >
              Rigenera
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost"
              onClick={() => {
                setProposal(null);
                setImportResult(null);
              }}
            >
              Annulla
            </button>
          </div>
        </section>
      )}

      <form onSubmit={handleSave}>
        <section className="bi-profile-block gcr-card">
          <h3 className="bi-panel__title">Brand Identity ufficiale</h3>
          <p className="bi-panel__subtitle">
            Dati salvati ufficialmente. Aggiornati dopo Applica proposta o salvataggio manuale.
          </p>
          {renderIdentityFields(form, setForm, "official")}
          <div className="bi-profile-actions">
            <button type="submit" className="gcr-btn gcr-btn--primary" disabled={update.isPending}>
              {update.isPending ? "Salvataggio…" : "Salva Brand Identity"}
            </button>
          </div>
        </section>
      </form>
    </div>
  );
}
