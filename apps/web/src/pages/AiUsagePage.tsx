import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { AiUsageLog } from "@gcr/shared";
import { PageHeader } from "../components/PageHeader";
import { MetricCard } from "../components/MetricCard";
import { DateRangeSelector } from "../components/DateRangeSelector";
import { StatusBadge } from "../components/StatusBadge";
import { AppModal } from "../components/ui/AppModal";
import { useDateRangeParams } from "../hooks/useDateRangeParams";
import { useAiBudgetStatus, useAiUsageLog, useAiUsageLogs, useAiUsageSummary } from "../hooks/useAiUsage";

const MODULE_OPTIONS = [
  { value: "", label: "Tutti i moduli" },
  { value: "brand_intelligence", label: "Brand Intelligence" },
  { value: "product_seo", label: "Product SEO" },
  { value: "content_seo", label: "Content SEO" },
  { value: "blog_brief", label: "Blog Brief" },
  { value: "article_generator", label: "Article Generator" },
];

function formatCost(value: number | null | undefined): string {
  if (value == null) return "—";
  return `$${value.toFixed(4)}`;
}

function formatTokens(n: number): string {
  return n.toLocaleString("it-IT");
}

function formatContextBlocks(blocks: string[] | null | undefined): string {
  if (!blocks?.length) return "—";
  const labels: Record<string, string> = {
    brand_profile: "Brand Profile",
    brand_identity: "Brand Identity",
    visual_identity: "Visual Identity",
    tone: "Tono",
    safe_claims: "Safe Claims",
    product_knowledge_general: "Product Knowledge (generale)",
    product_knowledge_specific: "Product Knowledge (specifica)",
    faq_objections: "FAQ & Obiezioni",
    faq_selected: "FAQ selezionate",
    editorial_guidelines: "Editorial Guidelines",
    editorial_item: "Item editoriale",
    approved_brief: "Brief approvato",
    entity_product: "Prodotto",
    entity_collection: "Collection",
    brand_import_schema: "Schema import",
    text_to_review: "Testo da valutare",
  };
  return blocks.map((b) => labels[b] ?? b).join(", ");
}

function LogDetailModal({
  open,
  projectId,
  logId,
  onClose,
}: {
  open: boolean;
  projectId: string;
  logId: string | null;
  onClose: () => void;
}) {
  const { data: log, isLoading } = useAiUsageLog(projectId, logId);

  return (
    <AppModal open={open} onClose={onClose} title="Dettaglio richiesta AI">
      {isLoading && <div className="gcr-skeleton" style={{ height: 120 }} />}
      {log && (
        <div className="ai-usage-detail">
          <dl className="ai-usage-detail__grid">
            <div><dt>Modulo</dt><dd>{log.module}</dd></div>
            <div><dt>Operazione</dt><dd>{log.operation}</dd></div>
            <div><dt>Modello</dt><dd>{log.model}</dd></div>
            <div><dt>Stato</dt><dd>{log.status}</dd></div>
            <div><dt>Entity</dt><dd>{log.entityType ?? "—"} {log.entityId ?? ""}</dd></div>
            <div><dt>Job</dt><dd>{log.jobId ?? "—"}</dd></div>
            <div><dt>Token input</dt><dd>{formatTokens(log.inputTokens)}</dd></div>
            <div><dt>Token output</dt><dd>{formatTokens(log.outputTokens)}</dd></div>
            <div><dt>Cached</dt><dd>{formatTokens(log.cachedInputTokens)}</dd></div>
            <div><dt>Costo stimato</dt><dd>{formatCost(log.estimatedTotalCost)}</dd></div>
            <div><dt>Durata</dt><dd>{log.durationMs != null ? `${log.durationMs} ms` : "—"}</dd></div>
            <div><dt>Response ID</dt><dd>{log.responseId ?? "—"}</dd></div>
            <div><dt>Context profile</dt><dd>{log.contextProfile ?? "—"}</dd></div>
            <div><dt>Context chars</dt><dd>{log.contextChars != null ? formatTokens(log.contextChars) : "—"}</dd></div>
            <div><dt>Context hash</dt><dd>{log.contextHash ?? "—"}</dd></div>
            <div><dt>Blocchi contesto</dt><dd>{formatContextBlocks(log.contextBlocksUsed)}</dd></div>
          </dl>
          {log.contextProfile && (
            <div className="ai-usage-detail__insight gcr-alert gcr-alert--info">
              Questo task ha usato il profilo: <strong>{log.contextProfile}</strong>
              {log.contextBlocksUsed && log.contextBlocksUsed.length > 0 && (
                <> — Blocchi usati: {formatContextBlocks(log.contextBlocksUsed)}</>
              )}
            </div>
          )}
          {log.promptPreview && (
            <div className="ai-usage-detail__block">
              <h4>Prompt preview</h4>
              <pre>{log.promptPreview}</pre>
            </div>
          )}
          {log.outputPreview && (
            <div className="ai-usage-detail__block">
              <h4>Output preview</h4>
              <pre>{log.outputPreview}</pre>
            </div>
          )}
          {log.errorMessage && (
            <div className="gcr-alert gcr-alert--error">{log.errorMessage}</div>
          )}
        </div>
      )}
    </AppModal>
  );
}

export function AiUsagePage() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  const { dateRange, setDateRange } = useDateRangeParams();
  const [moduleFilter, setModuleFilter] = useState("");
  const [operationFilter, setOperationFilter] = useState("");
  const [modelFilter, setModelFilter] = useState("");
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);

  const filters = useMemo(
    () => ({
      dateRange,
      module: moduleFilter || undefined,
      operation: operationFilter || undefined,
      model: modelFilter || undefined,
    }),
    [dateRange, moduleFilter, operationFilter, modelFilter],
  );

  const summaryQuery = useAiUsageSummary(projectId, filters);
  const logsQuery = useAiUsageLogs(projectId, { ...filters, limit: 30 });
  const budgetQuery = useAiBudgetStatus(projectId);

  const summary = summaryQuery.data;
  const logs = logsQuery.data?.items ?? [];
  const avgCost =
    summary && summary.totalRequests > 0
      ? summary.totalEstimatedCost / summary.totalRequests
      : 0;

  const dayChartData = (summary?.byDay ?? []).map((d) => ({
    date: d.date?.slice(5) ?? "",
    cost: d.estimatedCost,
  }));

  const moduleChartData = (summary?.byModule ?? []).slice(0, 8).map((m) => ({
    name: m.key ?? "?",
    cost: m.estimatedCost,
  }));

  return (
    <motion.div
      className="ai-usage-page"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <PageHeader
        title="AI Usage Monitor"
        subtitle="Controlla richieste AI, token e costo stimato per modulo."
      />

      {budgetQuery.data?.nearLimit && !budgetQuery.data.blocked && (
        <div className="gcr-alert gcr-alert--warning ai-usage-page__budget-banner">
          Budget AI vicino al limite — giornaliero: ${budgetQuery.data.dailySpent.toFixed(2)}
          {budgetQuery.data.dailyBudgetUsd != null && ` / $${budgetQuery.data.dailyBudgetUsd}`},
          mensile: ${budgetQuery.data.monthlySpent.toFixed(2)}
          {budgetQuery.data.monthlyBudgetUsd != null && ` / $${budgetQuery.data.monthlyBudgetUsd}`}.
        </div>
      )}
      {budgetQuery.data?.blocked && (
        <div className="gcr-alert gcr-alert--error ai-usage-page__budget-banner">
          Budget AI superato. Nuove generazioni AI sono bloccate fino al reset del periodo.
        </div>
      )}

      <div className="ai-usage-page__toolbar">
        <DateRangeSelector value={dateRange} onChange={setDateRange} />
        <select
          className="gcr-input"
          value={moduleFilter}
          onChange={(e) => setModuleFilter(e.target.value)}
          aria-label="Filtra modulo"
        >
          {MODULE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <input
          className="gcr-input"
          type="text"
          placeholder="Operazione"
          value={operationFilter}
          onChange={(e) => setOperationFilter(e.target.value)}
        />
        <input
          className="gcr-input"
          type="text"
          placeholder="Modello"
          value={modelFilter}
          onChange={(e) => setModelFilter(e.target.value)}
        />
      </div>

      {summaryQuery.isLoading ? (
        <div className="gcr-skeleton ai-usage-page__skeleton" />
      ) : summaryQuery.isError ? (
        <div className="gcr-alert gcr-alert--error">Impossibile caricare i dati AI usage.</div>
      ) : summary ? (
        <>
          <div className="gcr-grid gcr-grid--4 ai-usage-page__kpis">
            <MetricCard label="Costo stimato periodo" value={formatCost(summary.totalEstimatedCost)} />
            <MetricCard label="Richieste totali" value={summary.totalRequests} />
            <MetricCard label="Token input" value={formatTokens(summary.totalInputTokens)} />
            <MetricCard label="Token output" value={formatTokens(summary.totalOutputTokens)} />
            <MetricCard label="Token cached" value={formatTokens(summary.totalCachedInputTokens)} />
            <MetricCard label="Errori" value={summary.failedRequests} />
            <MetricCard label="Costo medio / richiesta" value={formatCost(avgCost)} />
            <MetricCard
              label="Successo"
              value={`${summary.successfulRequests}/${summary.totalRequests}`}
            />
          </div>

          <div className="gcr-grid gcr-grid--2 ai-usage-page__charts">
            <div className="gcr-card">
              <h3 className="gcr-card__title">Costo per giorno</h3>
              {dayChartData.length === 0 ? (
                <p className="gcr-card__description">Nessun dato nel periodo.</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={dayChartData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis dataKey="date" fontSize={11} />
                    <YAxis fontSize={11} tickFormatter={(v) => `$${v}`} />
                    <Tooltip formatter={(v: number) => formatCost(v)} />
                    <Bar dataKey="cost" fill="var(--gcr-accent, #6366f1)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
            <div className="gcr-card">
              <h3 className="gcr-card__title">Costo per modulo</h3>
              {moduleChartData.length === 0 ? (
                <p className="gcr-card__description">Nessun dato nel periodo.</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={moduleChartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                    <XAxis type="number" fontSize={11} tickFormatter={(v) => `$${v}`} />
                    <YAxis type="category" dataKey="name" width={100} fontSize={10} />
                    <Tooltip formatter={(v: number) => formatCost(v)} />
                    <Bar dataKey="cost" fill="var(--gcr-accent-2, #8b5cf6)" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="gcr-card ai-usage-page__table-card">
            <h3 className="gcr-card__title">Ultime richieste AI</h3>
            {logs.length === 0 ? (
              <p className="gcr-card__description">Nessuna richiesta registrata nel periodo.</p>
            ) : (
              <div className="ai-usage-table-wrap">
                <table className="ai-usage-table">
                  <thead>
                    <tr>
                      <th>Data/ora</th>
                      <th>Modulo</th>
                      <th>Profilo</th>
                      <th>Operazione</th>
                      <th>Modello</th>
                      <th>In</th>
                      <th>Out</th>
                      <th>Cached</th>
                      <th>Costo</th>
                      <th>Stato</th>
                      <th>Durata</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((row: AiUsageLog) => (
                      <tr
                        key={row.id}
                        className="ai-usage-table__row"
                        onClick={() => setSelectedLogId(row.id)}
                      >
                        <td>{new Date(row.createdAt).toLocaleString("it-IT")}</td>
                        <td>{row.module}</td>
                        <td>{row.contextProfile ?? "—"}</td>
                        <td>{row.operation}</td>
                        <td>{row.model}</td>
                        <td>{row.inputTokens}</td>
                        <td>{row.outputTokens}</td>
                        <td>{row.cachedInputTokens}</td>
                        <td>{formatCost(row.estimatedTotalCost)}</td>
                        <td>
                          <StatusBadge
                            variant={row.status === "success" ? "active" : "error"}
                            label={row.status === "success" ? "OK" : "Errore"}
                          />
                        </td>
                        <td>{row.durationMs != null ? `${row.durationMs}ms` : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      ) : null}

      <LogDetailModal
        open={Boolean(selectedLogId)}
        projectId={projectId}
        logId={selectedLogId}
        onClose={() => setSelectedLogId(null)}
      />
    </motion.div>
  );
}
