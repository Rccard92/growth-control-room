import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import type { DataForSeoEstimateMode, DataForSeoTestType } from "@gcr/shared";
import { MetricCard } from "../components/MetricCard";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import {
  useDataForSeoEstimate,
  useDataForSeoSandboxTest,
  useDataForSeoStatus,
  useDataForSeoUsage,
} from "../hooks/useDataForSeo";
import { useGrowthAuditRuns } from "../hooks/useGrowthAudit";
import { useProject } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";

const ESTIMATE_MODES: { value: DataForSeoEstimateMode; label: string }[] = [
  { value: "single_page", label: "Micro (1 prodotto)" },
  { value: "top_10_products", label: "Small batch (top 10)" },
  { value: "full_site", label: "Full controlled (tutto il sito)" },
];

const TEST_TYPES: { value: DataForSeoTestType; label: string }[] = [
  { value: "search_volume", label: "Search volume" },
  { value: "keyword_ideas", label: "Keyword ideas" },
  { value: "serp", label: "SERP top 10" },
  { value: "micro_bundle", label: "Micro bundle" },
];

function formatUsd(value: number | null | undefined): string {
  if (value == null) return "—";
  return `$${value.toFixed(4)}`;
}

export function formatDataForSeoTestError(err: unknown): string {
  if (!(err instanceof Error)) {
    return "Test non riuscito.";
  }
  const lowered = err.message.toLowerCase();
  if (
    lowered.includes("field required")
    || lowered.includes("unprocessable")
    || lowered.includes("validation")
    || lowered.includes("422")
  ) {
    return "Payload non valido: controlla keyword, location e lingua.";
  }
  return err.message || "Test non riuscito.";
}

export function DataForSeoCostSandboxPage() {
  const { id: projectId } = useParams<{ id: string }>();
  const { data: project } = useProject(projectId);
  const { data: status, isLoading: isStatusLoading } = useDataForSeoStatus(projectId);
  const { data: usage, isLoading: isUsageLoading } = useDataForSeoUsage(projectId);
  const { data: runs } = useGrowthAuditRuns(projectId);
  const estimateMutation = useDataForSeoEstimate(projectId);
  const testMutation = useDataForSeoSandboxTest(projectId);

  const [keyword, setKeyword] = useState("polline biologico");
  const [locationCode, setLocationCode] = useState(2380);
  const [languageCode, setLanguageCode] = useState("it");
  const [testType, setTestType] = useState<DataForSeoTestType>("search_volume");
  const [estimateMode, setEstimateMode] = useState<DataForSeoEstimateMode>("single_page");
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [testError, setTestError] = useState<string | null>(null);

  const completedRuns = useMemo(
    () => (runs ?? []).filter((run) => run.status === "completed"),
    [runs],
  );

  const testDisabled =
    !status?.configured ||
    !status.realCallsEnabled ||
    testMutation.isPending ||
    !keyword.trim();

  const handleEstimate = async () => {
    if (!projectId) return;
    await estimateMutation.mutateAsync({
      mode: estimateMode,
      runId: selectedRunId || undefined,
    });
  };

  const handleTest = async () => {
    if (!projectId) return;
    setTestError(null);

    const trimmedKeyword = keyword.trim();
    if (!trimmedKeyword) {
      setTestError("Inserisci una keyword.");
      return;
    }
    if (!Number.isFinite(locationCode) || locationCode < 1) {
      setTestError("Location code non valido.");
      return;
    }
    const trimmedLanguage = languageCode.trim();
    if (!trimmedLanguage) {
      setTestError("Inserisci una lingua.");
      return;
    }

    try {
      await testMutation.mutateAsync({
        testType,
        keyword: trimmedKeyword,
        locationCode,
        languageCode: trimmedLanguage,
      });
    } catch (error) {
      setTestError(formatDataForSeoTestError(error));
    }
  };

  const estimate = estimateMutation.data;
  const testResult = testMutation.data;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="DataForSEO Cost Sandbox"
        subtitle="Test controllati e stima costi pay-as-you-go prima di integrazioni massive."
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? projectId ?? "", href: projectId ? APP_ROUTES.project(projectId) : undefined },
          { label: "Integrazioni", href: projectId ? APP_ROUTES.projectIntegrations(projectId) : undefined },
          { label: "DataForSEO" },
        ]}
      />

      <section className="gcr-panel" style={{ marginBottom: "1.5rem" }}>
        <div className="gcr-panel__header">
          <h2 className="gcr-panel__title">Status integrazione</h2>
        </div>
        {isStatusLoading && <div className="gcr-skeleton" style={{ height: 80 }} />}
        {!isStatusLoading && status && (
          <div className="gcr-grid gcr-grid--auto" style={{ marginBottom: "1rem" }}>
            <MetricCard
              label="Configurazione"
              value={status.configured ? "Configurata" : "Non configurata"}
            />
            <MetricCard
              label="Real calls"
              value={status.realCallsEnabled ? "Abilitate" : "Disabilitate"}
            />
            <MetricCard label="Budget giornaliero" value={formatUsd(status.dailyBudgetUsd)} />
            <MetricCard label="Usage oggi" value={formatUsd(status.usageTodayUsd)} />
            <MetricCard label="Usage mese" value={formatUsd(status.usageMonthUsd)} />
          </div>
        )}
        {status && (
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
            <StatusBadge
              variant={status.configured ? "connected" : "missing_credentials"}
              label={status.configured ? "Configurata" : "Credenziali mancanti"}
            />
            {status.configured && !status.realCallsEnabled && (
              <StatusBadge variant="needs_setup" label="Real calls disabilitate" />
            )}
            {status.missingVars.length > 0 && (
              <span className="gcr-muted">Mancano: {status.missingVars.join(", ")}</span>
            )}
          </div>
        )}
      </section>

      <section className="gcr-panel" style={{ marginBottom: "1.5rem" }}>
        <div className="gcr-panel__header">
          <h2 className="gcr-panel__title">Test manuale controllato</h2>
        </div>
        <div className="gcr-form-grid">
          <label className="gcr-field">
            <span className="gcr-field__label">Keyword</span>
            <input
              className="gcr-input"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="polline biologico"
            />
          </label>
          <label className="gcr-field">
            <span className="gcr-field__label">Location code</span>
            <input
              className="gcr-input"
              type="number"
              value={locationCode}
              onChange={(event) => setLocationCode(Number(event.target.value))}
            />
          </label>
          <label className="gcr-field">
            <span className="gcr-field__label">Language</span>
            <input
              className="gcr-input"
              value={languageCode}
              onChange={(event) => setLanguageCode(event.target.value)}
            />
          </label>
          <label className="gcr-field">
            <span className="gcr-field__label">Tipo test</span>
            <select
              className="gcr-input"
              value={testType}
              onChange={(event) => setTestType(event.target.value as DataForSeoTestType)}
            >
              {TEST_TYPES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        {!status?.realCallsEnabled && (
          <div className="gcr-alert gcr-alert--error" style={{ marginTop: "1rem" }}>
            Le chiamate reali sono disabilitate. Imposta DATAFORSEO_ENABLE_REAL_CALLS=true sul backend
            per eseguire test a pagamento.
          </div>
        )}
        {testError && (
          <div className="gcr-alert gcr-alert--error" style={{ marginTop: "1rem" }}>
            {testError}
          </div>
        )}
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          style={{ marginTop: "1rem" }}
          disabled={testDisabled}
          onClick={() => void handleTest()}
        >
          {testMutation.isPending ? "Esecuzione..." : "Esegui test controllato"}
        </button>
      </section>

      {testResult && (
        <section className="gcr-panel" style={{ marginBottom: "1.5rem" }}>
          <div className="gcr-panel__header">
            <h2 className="gcr-panel__title">Risultato test</h2>
          </div>
          <p>
            <strong>Costo:</strong> {formatUsd(testResult.costUsd)}
          </p>
          <p>
            <strong>Endpoint:</strong> {testResult.endpoints.join(", ")}
          </p>
          {testResult.responseSummary && (
            <pre className="gcr-code-block" style={{ marginTop: "0.75rem" }}>
              {JSON.stringify(testResult.responseSummary, null, 2)}
            </pre>
          )}
          {testResult.rawPreview && (
            <details style={{ marginTop: "0.75rem" }}>
              <summary>Raw preview</summary>
              <pre className="gcr-code-block">
                {JSON.stringify(testResult.rawPreview, null, 2)}
              </pre>
            </details>
          )}
        </section>
      )}

      <section className="gcr-panel" style={{ marginBottom: "1.5rem" }}>
        <div className="gcr-panel__header">
          <h2 className="gcr-panel__title">Stima sito (solo calcolo)</h2>
        </div>
        <div className="gcr-form-grid">
          <label className="gcr-field">
            <span className="gcr-field__label">Run Growth Audit</span>
            <select
              className="gcr-input"
              value={selectedRunId}
              onChange={(event) => setSelectedRunId(event.target.value)}
            >
              <option value="">Nessun run (usa preset)</option>
              {completedRuns.map((run) => (
                <option key={run.id} value={run.id}>
                  {run.normalizedDomain} —{" "}
                  {new Date(run.createdAt ?? run.id).toLocaleDateString("it-IT")}
                </option>
              ))}
            </select>
          </label>
          <label className="gcr-field">
            <span className="gcr-field__label">Modalità</span>
            <select
              className="gcr-input"
              value={estimateMode}
              onChange={(event) => setEstimateMode(event.target.value as DataForSeoEstimateMode)}
            >
              {ESTIMATE_MODES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary"
          style={{ marginTop: "1rem" }}
          disabled={estimateMutation.isPending}
          onClick={() => void handleEstimate()}
        >
          {estimateMutation.isPending ? "Calcolo..." : "Calcola stima"}
        </button>
        {estimate && (
          <div style={{ marginTop: "1rem" }}>
            <p>
              <strong>Chiamate previste:</strong> search volume {estimate.estimatedCalls.searchVolume},{" "}
              keyword ideas {estimate.estimatedCalls.keywordIdeas}, SERP {estimate.estimatedCalls.serp}
            </p>
            <p>
              <strong>Costo stimato:</strong> {formatUsd(estimate.estimatedCostUsd)}
            </p>
            {estimate.auditContext && (
              <p className="gcr-muted">
                Contesto audit: {estimate.auditContext.productPagesCount} pagine prodotto,{" "}
                {estimate.auditContext.pagesWithGscQueries} con query GSC.
              </p>
            )}
            {estimate.budgetWarnings.length > 0 && (
              <div className="gcr-alert gcr-alert--error" style={{ marginTop: "0.75rem" }}>
                {estimate.budgetWarnings.map((warning) => (
                  <div key={warning}>{warning}</div>
                ))}
              </div>
            )}
            <ul className="gcr-muted" style={{ marginTop: "0.75rem" }}>
              {estimate.assumptions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section className="gcr-panel">
        <div className="gcr-panel__header">
          <h2 className="gcr-panel__title">Usage log</h2>
        </div>
        {isUsageLoading && <div className="gcr-skeleton" style={{ height: 120 }} />}
        {!isUsageLoading && usage && (
          <>
            <p className="gcr-muted" style={{ marginBottom: "0.75rem" }}>
              Oggi: {formatUsd(usage.usageTodayUsd)} — Mese: {formatUsd(usage.usageMonthUsd)}
            </p>
            {usage.logs.length === 0 ? (
              <p className="gcr-muted">Nessuna chiamata registrata.</p>
            ) : (
              <div className="gcr-table-wrap">
                <table className="gcr-table">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Operation</th>
                      <th>Endpoint</th>
                      <th>Status</th>
                      <th>Costo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usage.logs.map((log) => (
                      <tr key={log.id}>
                        <td>{new Date(log.createdAt).toLocaleString("it-IT")}</td>
                        <td>{log.operation}</td>
                        <td>{log.endpoint}</td>
                        <td>{log.status}</td>
                        <td>{formatUsd(log.costUsd)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </section>

      {projectId && (
        <p style={{ marginTop: "1.5rem" }}>
          <Link className="gcr-link" to={APP_ROUTES.projectIntegrations(projectId)}>
            ← Torna a Integration Center
          </Link>
        </p>
      )}
    </motion.div>
  );
}
