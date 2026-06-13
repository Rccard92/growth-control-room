import { useEffect, useState } from "react";
import type { BrandIntelligenceBrief } from "@gcr/shared";
import { BrandIntelligenceBriefEditor } from "./BrandIntelligenceBriefEditor";
import {
  useApproveBrandBrief,
  useArchiveBrandBrief,
  useGenerateBrandBrief,
  usePatchBrandBrief,
} from "../../hooks/useBrandIntelligence";

interface BrandIntelligenceBriefPanelProps {
  projectId: string;
  batchId: string | null;
  brief: BrandIntelligenceBrief | undefined;
  briefLoadFailed?: boolean;
  onBriefGenerated: (briefId: string) => void;
  onRegenerate?: () => void;
}

export function BrandIntelligenceBriefPanel({
  projectId,
  batchId,
  brief,
  briefLoadFailed = false,
  onBriefGenerated,
}: BrandIntelligenceBriefPanelProps) {
  const [editing, setEditing] = useState(false);
  const [editPayload, setEditPayload] = useState(brief?.briefPayload ?? {});
  const generate = useGenerateBrandBrief(projectId);
  const patch = usePatchBrandBrief(projectId);
  const approve = useApproveBrandBrief(projectId);
  const archive = useArchiveBrandBrief(projectId);

  useEffect(() => {
    if (brief) setEditPayload(brief.briefPayload);
  }, [brief]);

  const payload = brief?.briefPayload ?? {};
  const warnings = (brief?.warnings as { messages?: string[] } | null)?.messages ?? [];
  const missing = (payload.missing_information as string[] | undefined) ?? [];
  const sourceWarnings = (payload.source_warnings as string[] | undefined) ?? [];

  async function handleGenerate() {
    if (!batchId) return;
    const result = await generate.mutateAsync(batchId);
    onBriefGenerated(result.briefId);
  }

  async function handleSave() {
    if (!brief) return;
    await patch.mutateAsync({
      briefId: brief.id,
      data: { briefPayload: editPayload },
    });
    setEditing(false);
  }

  if (briefLoadFailed) {
    return (
      <div className="bi-brief-panel gcr-card">
        <div className="gcr-alert gcr-alert--error">
          Impossibile aprire il Brand Intelligence Brief. Riprova.
        </div>
        {batchId && (
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            style={{ marginTop: "1rem" }}
            disabled={generate.isPending}
            onClick={() => void handleGenerate()}
          >
            {generate.isPending ? "Generazione in corso…" : "Rigenera Brand Intelligence Brief"}
          </button>
        )}
      </div>
    );
  }

  if (!brief) {
    return (
      <div className="bi-brief-panel gcr-card">
        <h3 className="bi-panel__title">Brand Intelligence Brief</h3>
        <p className="bi-panel__subtitle">
          Genera un brief unico e flessibile da file, facts e fonti esterne. Nessun dato diventa
          ufficiale finché non approvi il brief.
        </p>
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          disabled={!batchId || generate.isPending}
          onClick={() => void handleGenerate()}
        >
          {generate.isPending ? "Generazione in corso…" : "Genera Brand Intelligence Brief"}
        </button>
        {generate.isError && (
          <div className="gcr-alert gcr-alert--error" style={{ marginTop: "1rem" }}>
            {generate.error instanceof Error ? generate.error.message : "Generazione fallita."}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bi-brief-panel">
      <div className="bi-brief-panel__header gcr-card">
        <div>
          <h3 className="bi-panel__title">{brief.title}</h3>
          <p className="bi-panel__subtitle">
            Versione {brief.version}
            {brief.confidence != null && ` · Confidence ${Math.round(brief.confidence * 100)}%`}
          </p>
        </div>
        {brief.status === "approved" && (
          <span className="bi-brief-badge bi-brief-badge--active">Brief ufficiale attivo</span>
        )}
        {brief.status === "draft" && (
          <span className="bi-brief-badge">Bozza</span>
        )}
      </div>

      <div className="bi-brief-panel__meta gcr-card">
        <p>
          <strong>Fonti:</strong> {(brief.sourceFactIds ?? []).length} facts ·{" "}
          {(brief.sourceDocumentIds ?? []).length} documenti ·{" "}
          {(brief.sourceExternalIds ?? []).length} fonti esterne
        </p>
        {(warnings.length > 0 || sourceWarnings.length > 0) && (
          <div className="bi-brief-panel__warnings">
            <strong>Warning</strong>
            <ul>
              {[...warnings, ...sourceWarnings].map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}
        {missing.length > 0 && (
          <div className="bi-brief-panel__missing">
            <strong>Informazioni mancanti</strong>
            <ul>
              {missing.map((m, i) => (
                <li key={i}>{m}</li>
              ))}
            </ul>
          </div>
        )}
        {brief.markdownSummary && (
          <pre className="bi-brief-panel__summary">{brief.markdownSummary}</pre>
        )}
      </div>

      <div className="bi-brief-panel__actions bi-wizard__actions">
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          onClick={() => setEditing((v) => !v)}
        >
          {editing ? "Chiudi editor" : "Apri e modifica brief"}
        </button>
        {brief.status === "draft" && (
          <button
            type="button"
            className="gcr-btn gcr-btn--ghost"
            disabled={approve.isPending}
            onClick={() => approve.mutate(brief.id)}
          >
            {approve.isPending ? "Approvazione…" : "Approva brief"}
          </button>
        )}
        <button
          type="button"
          className="gcr-btn gcr-btn--ghost"
          disabled={!batchId || generate.isPending}
          onClick={() => void handleGenerate()}
        >
          Rigenera brief
        </button>
        {brief.status !== "archived" && (
          <button
            type="button"
            className="gcr-btn gcr-btn--ghost"
            disabled={archive.isPending}
            onClick={() => archive.mutate(brief.id)}
          >
            Archivia
          </button>
        )}
      </div>

      {editing && (
        <div className="gcr-card" style={{ marginTop: "1rem" }}>
          <BrandIntelligenceBriefEditor
            payload={editPayload}
            onChange={setEditPayload}
          />
          <div className="bi-wizard__actions" style={{ marginTop: "1rem" }}>
            <button
              type="button"
              className="gcr-btn gcr-btn--primary gcr-btn--sm"
              disabled={patch.isPending}
              onClick={() => void handleSave()}
            >
              Salva modifiche
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
