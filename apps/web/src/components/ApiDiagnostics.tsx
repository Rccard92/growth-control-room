import { useState } from "react";
import { runApiDiagnostics, type ApiDiagnosticsResult } from "../lib/apiDiagnostics";

function statusLabel(status: "ok" | "fail" | "skipped"): string {
  if (status === "ok") return "OK";
  if (status === "fail") return "Errore";
  return "Saltato";
}

export function ApiDiagnostics() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ApiDiagnosticsResult | null>(null);

  async function handleRun() {
    setOpen(true);
    setLoading(true);
    try {
      setResult(await runApiDiagnostics());
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="gcr-card" style={{ marginTop: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "1rem" }}>
        <div>
          <p className="gcr-card__label" style={{ margin: 0 }}>Diagnostica API</p>
          <p style={{ margin: "0.375rem 0 0", fontSize: "0.8125rem", color: "var(--gcr-text-muted)" }}>
            Verifica rapida di health e progetti
          </p>
        </div>
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary"
          onClick={handleRun}
          disabled={loading}
        >
          {loading ? "Verifica…" : "Verifica connessione API"}
        </button>
      </div>

      {open && result && (
        <div style={{ marginTop: "1rem", fontSize: "0.8125rem", color: "var(--gcr-text-muted)" }}>
          <p style={{ margin: "0 0 0.5rem" }}>
            <strong>API base:</strong> {result.apiBase}
          </p>
          <p style={{ margin: "0 0 0.25rem" }}>
            GET /api/health — {statusLabel(result.health)}
          </p>
          <p style={{ margin: "0 0 0.5rem" }}>
            GET /api/projects — {statusLabel(result.projects)}
          </p>
          {result.detail && (
            <p className="gcr-alert gcr-alert--error" style={{ margin: 0 }}>
              {result.detail}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
