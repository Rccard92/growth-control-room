import { useEffect, useMemo, useState } from "react";
import type { AiModelSettingItem } from "@gcr/shared";
import { AppModal } from "./ui/AppModal";
import {
  useAiModelSettings,
  useResetAiModelSetting,
  useUpdateAiModelSetting,
} from "../hooks/useAiModelSettings";

const TIER_OPTIONS = ["cheap", "standard", "premium", "reasoning", "fallback"];

function statusLabel(status: string): string {
  if (status === "implemented") return "Attivo";
  if (status === "planned") return "Pianificato";
  return "Non AI";
}

function EditSettingModal({
  open,
  item,
  modelOptions,
  onClose,
  onSave,
  saving,
}: {
  open: boolean;
  item: AiModelSettingItem | null;
  modelOptions: string[];
  onClose: () => void;
  onSave: (body: { model: string; modelTier: string; maxOutputTokens: number; temperature: number }) => void;
  saving: boolean;
}) {
  const [model, setModel] = useState("");
  const [modelTier, setModelTier] = useState("standard");
  const [maxTokens, setMaxTokens] = useState(2000);
  const [temperature, setTemperature] = useState(0.45);

  useEffect(() => {
    if (item) {
      setModel(item.model ?? "");
      setModelTier(item.modelTier);
      setMaxTokens(item.maxOutputTokens ?? item.recommendedMaxOutputTokens);
      setTemperature(item.temperature ?? item.recommendedTemperature);
    }
  }, [item]);

  if (!item) return null;

  return (
    <AppModal open={open} onClose={onClose} title={`Modifica: ${item.label}`}>
      <div className="ai-model-settings-edit">
        <p className="gcr-card__description">{item.recommendedUse}</p>
        <label className="gcr-field">
          <span>Modello</span>
          <input
            className="gcr-input"
            list="ai-model-options"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          />
          <datalist id="ai-model-options">
            {modelOptions.map((m) => (
              <option key={m} value={m} />
            ))}
          </datalist>
        </label>
        <label className="gcr-field">
          <span>Tier</span>
          <select
            className="gcr-input"
            value={modelTier}
            onChange={(e) => setModelTier(e.target.value)}
          >
            {TIER_OPTIONS.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </label>
        <label className="gcr-field">
          <span>Max output tokens</span>
          <input
            className="gcr-input"
            type="number"
            value={maxTokens}
            onChange={(e) => setMaxTokens(Number(e.target.value))}
          />
        </label>
        <label className="gcr-field">
          <span>Temperature</span>
          <input
            className="gcr-input"
            type="number"
            step="0.05"
            min="0"
            max="1"
            value={temperature}
            onChange={(e) => setTemperature(Number(e.target.value))}
          />
        </label>
        <div className="ai-model-settings-edit__actions">
          <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
            Annulla
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={saving || !model.trim()}
            onClick={() => onSave({ model, modelTier, maxOutputTokens: maxTokens, temperature })}
          >
            Salva
          </button>
        </div>
      </div>
    </AppModal>
  );
}

export function AiModelSettingsPanel({ projectId }: { projectId: string }) {
  const { data, isLoading, isError } = useAiModelSettings(projectId);
  const updateMutation = useUpdateAiModelSetting(projectId);
  const resetMutation = useResetAiModelSetting(projectId);
  const [editItem, setEditItem] = useState<AiModelSettingItem | null>(null);

  const modelOptions = useMemo(
    () => (data?.availableModels.models ?? []).map((m) => m.name),
    [data],
  );

  const implemented = (data?.items ?? []).filter((i) => i.status === "implemented");
  const plannedOrNonAi = (data?.items ?? []).filter((i) => i.status !== "implemented");

  if (isLoading) return <div className="gcr-skeleton" style={{ height: 200 }} />;
  if (isError) return <div className="gcr-alert gcr-alert--error">Impossibile caricare Model Settings.</div>;

  return (
    <div className="ai-model-settings-panel">
      <div className="gcr-alert gcr-alert--info ai-model-settings-panel__banner">
        Le variabili Railway sono usate solo come default/fallback. Le scelte operative sono quelle salvate qui.
      </div>

      <div className="ai-usage-table-wrap">
        <table className="ai-usage-table">
          <thead>
            <tr>
              <th>Punto AI</th>
              <th>Stato</th>
              <th>Profilo</th>
              <th>Tier</th>
              <th>Modello</th>
              <th>Max tokens</th>
              <th>Temp</th>
              <th>Source</th>
              <th>Costo medio</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            {implemented.map((row) => (
              <tr key={row.operationKey}>
                <td>
                  <strong>{row.label}</strong>
                  <div className="ai-model-settings-panel__hint">{row.operationKey}</div>
                </td>
                <td>{statusLabel(row.status)}</td>
                <td>{row.contextProfile}</td>
                <td>{row.modelTier}</td>
                <td>{row.model ?? "—"}</td>
                <td>{row.maxOutputTokens ?? "—"}</td>
                <td>{row.temperature ?? "—"}</td>
                <td>{row.source}</td>
                <td>{row.avgCostRecent != null ? `$${row.avgCostRecent.toFixed(4)}` : "—"}</td>
                <td>
                  <button
                    type="button"
                    className="gcr-btn gcr-btn--ghost gcr-btn--sm"
                    onClick={() => setEditItem(row)}
                  >
                    Modifica
                  </button>
                  <button
                    type="button"
                    className="gcr-btn gcr-btn--ghost gcr-btn--sm"
                    disabled={resetMutation.isPending}
                    onClick={() => resetMutation.mutate(row.operationKey)}
                  >
                    Ripristina
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {plannedOrNonAi.length > 0 && (
        <div className="ai-model-settings-panel__planned">
          <h3 className="gcr-card__title">Pianificate / Non AI</h3>
          <div className="ai-usage-table-wrap">
            <table className="ai-usage-table">
              <thead>
                <tr>
                  <th>Punto AI</th>
                  <th>Stato</th>
                  <th>Profilo</th>
                  <th>Tier consigliato</th>
                  <th>Modello</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {plannedOrNonAi.map((row) => (
                  <tr key={row.operationKey}>
                    <td>
                      <strong>{row.label}</strong>
                      <div className="ai-model-settings-panel__hint">{row.operationKey}</div>
                    </td>
                    <td>{statusLabel(row.status)}</td>
                    <td>{row.contextProfile}</td>
                    <td>{row.recommendedTier}</td>
                    <td>—</td>
                    <td>{row.guardrailWarnings[0] ?? row.recommendedUse}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {(data?.items ?? []).some((i) => i.guardrailWarnings.length > 0) && (
        <div className="ai-model-settings-panel__warnings">
          {implemented
            .filter((i) => i.guardrailWarnings.length > 0)
            .map((i) => (
              <div key={i.operationKey} className="gcr-alert gcr-alert--warning">
                <strong>{i.label}:</strong> {i.guardrailWarnings.join(" ")}
              </div>
            ))}
        </div>
      )}

      <EditSettingModal
        open={Boolean(editItem)}
        item={editItem}
        modelOptions={modelOptions}
        onClose={() => setEditItem(null)}
        saving={updateMutation.isPending}
        onSave={(body) => {
          if (!editItem) return;
          updateMutation.mutate(
            { operationKey: editItem.operationKey, body },
            { onSuccess: () => setEditItem(null) },
          );
        }}
      />
    </div>
  );
}
