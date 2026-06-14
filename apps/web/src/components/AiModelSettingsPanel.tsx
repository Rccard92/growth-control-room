import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { AiModelSettingItem, AiModelUiCategory } from "@gcr/shared";
import { AppModal } from "./ui/AppModal";
import {
  useAiModelSettings,
  useApplyGcrRecommendations,
  useResetAiModelSetting,
  useResetModelsFromRailway,
  useUpdateAiModelSetting,
  useValidateAiModel,
} from "../hooks/useAiModelSettings";
import { updateAiModelSetting } from "../lib/ai-model-settings-api";
import { queryKeys } from "../lib/queryKeys";

const OTHER_MODEL_VALUE = "__other__";

const CATEGORY_ORDER: { id: AiModelUiCategory; label: string }[] = [
  { id: "brand_intelligence", label: "Brand Intelligence" },
  { id: "product_collection_seo", label: "Product & Collection SEO" },
  { id: "blog_articles", label: "Blog & Articoli" },
  { id: "ped_social", label: "PED & Social" },
  { id: "email_ads", label: "Email & Ads" },
  { id: "seo_advanced", label: "SEO Avanzata" },
];

const MODEL_SELECT_HINTS: Record<string, string> = {
  "gpt-5.4-nano": "massimo risparmio, solo test semplici",
  "gpt-5.4-mini": "consigliato per task brevi",
  "gpt-5.4": "equilibrio qualità/costo",
  "gpt-5.5": "alta qualità",
};

function modelOptionLabel(name: string): string {
  const hint = MODEL_SELECT_HINTS[name];
  return hint ? `${name} — ${hint}` : name;
}

function statusLabel(status: string): string {
  if (status === "planned") return "Pianificato";
  if (status === "non_ai") return "Non AI";
  return "Attivo";
}

function SettingRow({
  item,
  modelOptions,
  draftModel,
  onDraftChange,
  onSave,
  onReset,
  onTest,
  saving,
  resetting,
  testing,
  pricedModels,
  knownModels,
  testFeedback,
}: {
  item: AiModelSettingItem;
  modelOptions: string[];
  draftModel: string;
  onDraftChange: (value: string) => void;
  onSave: () => void;
  onReset: () => void;
  onTest: () => void;
  saving: boolean;
  resetting: boolean;
  testing: boolean;
  pricedModels: Set<string>;
  knownModels: Set<string>;
  testFeedback: string | null;
}) {
  const [useCustom, setUseCustom] = useState(
    () => Boolean(draftModel) && !modelOptions.includes(draftModel),
  );
  const savedModel = item.model ?? "";
  const isDirty = draftModel.trim() !== savedModel.trim();
  const selectValue = useCustom ? OTHER_MODEL_VALUE : (draftModel || modelOptions[0] || "");

  const handleSelectChange = (value: string) => {
    if (value === OTHER_MODEL_VALUE) {
      setUseCustom(true);
      if (modelOptions.includes(draftModel)) {
        onDraftChange("");
      }
      return;
    }
    setUseCustom(false);
    onDraftChange(value);
  };

  const rowUnpriced = Boolean(draftModel.trim()) && !pricedModels.has(draftModel.trim());
  const rowUnverified = Boolean(draftModel.trim()) && !knownModels.has(draftModel.trim());

  return (
    <article className="ai-models-row gcr-card">
      <div className="ai-models-row__main">
        <div className="ai-models-row__info">
          <h4 className="ai-models-row__title">{item.label}</h4>
          <p className="gcr-card__description">{item.description}</p>
          <p className="ai-models-row__gcr">
            <strong>Consiglio GCR:</strong> {item.gcrRecommendationReason}
            <span className="ai-models-row__gcr-model"> ({item.gcrRecommendedModel})</span>
          </p>
          <span className="ai-models-row__badge">{item.costProfileLabel}</span>
        </div>
        <div className="ai-models-row__controls">
          <label className="gcr-field">
            <span>Modello</span>
            <select
              className="gcr-input"
              value={selectValue}
              onChange={(e) => handleSelectChange(e.target.value)}
            >
              {modelOptions.map((m) => (
                <option key={m} value={m}>{modelOptionLabel(m)}</option>
              ))}
              <option value={OTHER_MODEL_VALUE}>Altro modello…</option>
            </select>
          </label>
          {useCustom && (
            <label className="gcr-field">
              <span>Nome modello</span>
              <input
                className="gcr-input"
                value={draftModel}
                onChange={(e) => onDraftChange(e.target.value)}
                placeholder="es. gpt-5.4-mini"
              />
            </label>
          )}
          {rowUnpriced && (
            <p className="ai-models-row__warn">Pricing non configurato per questo modello.</p>
          )}
          {rowUnverified && (
            <p className="ai-models-row__warn">Modello non verificato.</p>
          )}
          {item.guardrailWarnings.map((warning) => (
            <p key={warning} className="ai-models-row__warn">{warning}</p>
          ))}
          {testFeedback && (
            <p className="ai-models-row__warn">{testFeedback}</p>
          )}
          <div className="ai-models-row__actions">
            <button
              type="button"
              className="gcr-btn gcr-btn--primary gcr-btn--sm"
              disabled={saving || !isDirty || !draftModel.trim()}
              onClick={onSave}
            >
              Salva
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              disabled={testing || !draftModel.trim()}
              onClick={onTest}
            >
              Test modello
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost gcr-btn--sm"
              disabled={resetting}
              onClick={onReset}
            >
              Ripristina consigliato
            </button>
          </div>
        </div>
      </div>
      <details className="ai-models-row__advanced">
        <summary>Avanzate</summary>
        <dl className="ai-models-row__advanced-grid">
          <div><dt>Tier</dt><dd>{item.modelTier}</dd></div>
          <div><dt>Context profile</dt><dd>{item.contextProfile}</dd></div>
          <div><dt>Source</dt><dd>{item.source}</dd></div>
          <div><dt>Max output tokens</dt><dd>{item.maxOutputTokens ?? "—"}</dd></div>
          <div><dt>Temperature</dt><dd>{item.temperature ?? "—"}</dd></div>
          <div><dt>Fallback</dt><dd>{item.fallbackModel ?? "—"}</dd></div>
          <div><dt>Operation key</dt><dd>{item.operationKey}</dd></div>
        </dl>
      </details>
    </article>
  );
}

export function AiModelSettingsPanel({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const { data, isLoading, isError } = useAiModelSettings(projectId);
  const updateMutation = useUpdateAiModelSetting(projectId);
  const resetMutation = useResetAiModelSetting(projectId);
  const applyGcrMutation = useApplyGcrRecommendations(projectId);
  const resetRailwayMutation = useResetModelsFromRailway(projectId);

  const validateMutation = useValidateAiModel(projectId);

  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [testFeedbackByKey, setTestFeedbackByKey] = useState<Record<string, string>>({});
  const [testingKey, setTestingKey] = useState<string | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<AiModelUiCategory | null>(
    "product_collection_seo",
  );
  const [confirmAction, setConfirmAction] = useState<"gcr" | "railway" | null>(null);
  const [savingAll, setSavingAll] = useState(false);
  const [saveFeedback, setSaveFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const implemented = useMemo(
    () => (data?.items ?? []).filter((i) => i.status === "implemented"),
    [data],
  );
  const futureItems = useMemo(
    () => (data?.items ?? []).filter((i) => i.status !== "implemented"),
    [data],
  );

  const modelOptions = useMemo(() => {
    const known = (data?.availableModels.models ?? []).filter((m) => m.knownSupported);
    const names = new Set<string>(known.map((m) => m.name));
    for (const item of data?.items ?? []) {
      if (item.model) names.add(item.model);
    }
    return Array.from(names).sort();
  }, [data]);

  const knownModels = useMemo(
    () => new Set(
      (data?.availableModels.models ?? [])
        .filter((m) => m.knownSupported)
        .map((m) => m.name),
    ),
    [data],
  );

  const pricedModels = useMemo(
    () => new Set(
      (data?.availableModels.models ?? [])
        .filter((m) => m.pricingConfigured)
        .map((m) => m.name),
    ),
    [data],
  );

  useEffect(() => {
    if (!data) return;
    const next: Record<string, string> = {};
    for (const item of data.items) {
      if (item.status === "implemented") {
        next[item.operationKey] = item.model ?? item.gcrRecommendedModel;
      }
    }
    setDrafts(next);
  }, [data]);

  const dirtyKeys = useMemo(
    () => implemented.filter((item) => {
      const draft = drafts[item.operationKey] ?? "";
      const saved = item.model ?? "";
      return draft.trim() !== saved.trim();
    }).map((i) => i.operationKey),
    [implemented, drafts],
  );

  const grouped = useMemo(() => {
    const map = new Map<AiModelUiCategory, AiModelSettingItem[]>();
    for (const cat of CATEGORY_ORDER) {
      map.set(cat.id, []);
    }
    for (const item of implemented) {
      const list = map.get(item.uiCategory) ?? [];
      list.push(item);
      map.set(item.uiCategory, list);
    }
    return map;
  }, [implemented]);

  const handleTestRow = (operationKey: string) => {
    const model = drafts[operationKey]?.trim();
    if (!model) return;
    setTestingKey(operationKey);
    setTestFeedbackByKey((prev) => {
      const next = { ...prev };
      delete next[operationKey];
      return next;
    });
    validateMutation.mutate(
      { model, operationKey, runProbe: true },
      {
        onSuccess: (result) => {
          const message = result.probeMessage
            ?? (result.valid ? "Modello OK." : result.warnings.join(" "));
          setTestFeedbackByKey((prev) => ({
            ...prev,
            [operationKey]: result.probeStatus === "ok"
              ? `Test OK: ${message}`
              : message,
          }));
        },
        onError: (err) => {
          setTestFeedbackByKey((prev) => ({
            ...prev,
            [operationKey]: err instanceof Error ? err.message : "Test modello fallito.",
          }));
        },
        onSettled: () => setTestingKey(null),
      },
    );
  };

  const handleSaveRow = (operationKey: string) => {
    const model = drafts[operationKey]?.trim();
    if (!model) return;
    setSaveFeedback(null);
    updateMutation.mutate(
      { operationKey, body: { model } },
      {
        onSuccess: () => {
          setSaveFeedback({ type: "success", message: "Modello aggiornato" });
        },
        onError: (err) => {
          setSaveFeedback({
            type: "error",
            message: err instanceof Error ? err.message : "Errore salvataggio modello",
          });
        },
      },
    );
  };

  const runSaveAll = async () => {
    if (dirtyKeys.length === 0) return;
    setSavingAll(true);
    setSaveFeedback(null);
    try {
      for (const key of dirtyKeys) {
        const model = drafts[key]?.trim();
        if (!model) continue;
        await updateAiModelSetting(projectId, key, { model });
      }
      await qc.invalidateQueries({ queryKey: queryKeys.aiModelSettings.list(projectId) });
      setSaveFeedback({ type: "success", message: "Modelli aggiornati" });
    } catch (err) {
      setSaveFeedback({
        type: "error",
        message: err instanceof Error ? err.message : "Errore salvataggio modello",
      });
    } finally {
      setSavingAll(false);
    }
  };

  if (isLoading) return <div className="gcr-skeleton" style={{ height: 200 }} />;
  if (isError) return <div className="gcr-alert gcr-alert--error">Impossibile caricare Modelli AI.</div>;

  return (
    <div className="ai-models-panel">
      <header className="ai-models-panel__header">
        <h2 className="gcr-card__title">Modelli AI</h2>
        <p className="gcr-card__description">
          Qui scegli quale modello usare per ogni funzione AI del progetto. Le variabili Railway
          servono solo come default/fallback.
        </p>
      </header>

      <div className="ai-models-panel__toolbar">
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary gcr-btn--sm"
          onClick={() => setConfirmAction("gcr")}
          disabled={applyGcrMutation.isPending}
        >
          Applica consigli GCR
        </button>
        <button
          type="button"
          className="gcr-btn gcr-btn--secondary gcr-btn--sm"
          onClick={() => setConfirmAction("railway")}
          disabled={resetRailwayMutation.isPending}
        >
          Ripristina da Railway
        </button>
        <button
          type="button"
          className="gcr-btn gcr-btn--primary gcr-btn--sm"
          disabled={savingAll || dirtyKeys.length === 0}
          onClick={() => void runSaveAll()}
        >
          Salva tutte le modifiche{dirtyKeys.length > 0 ? ` (${dirtyKeys.length})` : ""}
        </button>
      </div>

      {saveFeedback && (
        <div
          className={`gcr-alert ${
            saveFeedback.type === "success" ? "gcr-alert--success" : "gcr-alert--error"
          }`}
          role="status"
        >
          {saveFeedback.message}
        </div>
      )}

      {(data?.unpricedModels?.length ?? 0) > 0 && (
        <div className="gcr-alert gcr-alert--warning ai-models-panel__pricing-banner">
          Alcuni modelli non hanno pricing configurato:{" "}
          {data?.unpricedModels.join(", ")}. Aggiungi il pricing per calcolare i costi correttamente.
        </div>
      )}

      <div className="ai-models-panel__categories">
        {CATEGORY_ORDER.map((cat) => {
          const items = grouped.get(cat.id) ?? [];
          if (items.length === 0) return null;
          const open = expandedCategory === cat.id;
          return (
            <section key={cat.id} className="ai-models-category gcr-card">
              <button
                type="button"
                className="ai-models-category__toggle"
                onClick={() => setExpandedCategory(open ? null : cat.id)}
              >
                <span>{cat.label}</span>
                <span className="ai-models-category__count">{items.length}</span>
              </button>
              {open && (
                <div className="ai-models-category__body">
                  {items.map((item) => (
                    <SettingRow
                      key={item.operationKey}
                      item={item}
                      modelOptions={modelOptions}
                      draftModel={drafts[item.operationKey] ?? item.model ?? ""}
                      onDraftChange={(value) =>
                        setDrafts((prev) => ({ ...prev, [item.operationKey]: value }))
                      }
                      onSave={() => handleSaveRow(item.operationKey)}
                      onReset={() => resetMutation.mutate(item.operationKey)}
                      onTest={() => handleTestRow(item.operationKey)}
                      saving={updateMutation.isPending}
                      resetting={resetMutation.isPending}
                      testing={testingKey === item.operationKey}
                      pricedModels={pricedModels}
                      knownModels={knownModels}
                      testFeedback={testFeedbackByKey[item.operationKey] ?? null}
                    />
                  ))}
                </div>
              )}
            </section>
          );
        })}
      </div>

      {futureItems.length > 0 && (
        <details className="ai-models-panel__future gcr-card">
          <summary>Funzioni future ({futureItems.length})</summary>
          <ul className="ai-models-panel__future-list">
            {futureItems.map((item) => (
              <li key={item.operationKey} className="ai-models-panel__future-item">
                <strong>{item.label}</strong>
                <span className="ai-models-panel__future-status">{statusLabel(item.status)}</span>
                <p className="gcr-card__description">{item.description}</p>
                <p className="ai-models-row__gcr">
                  Consiglio GCR: {item.gcrRecommendationReason} ({item.gcrRecommendedModel})
                </p>
              </li>
            ))}
          </ul>
        </details>
      )}

      <AppModal
        open={confirmAction === "gcr"}
        onClose={() => setConfirmAction(null)}
        title="Applica consigli GCR"
      >
        <p className="gcr-card__description">
          Stai per aggiornare i modelli consigliati per tutte le funzioni AI attive.
        </p>
        <div className="ai-model-settings-edit__actions">
          <button type="button" className="gcr-btn gcr-btn--secondary" onClick={() => setConfirmAction(null)}>
            Annulla
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={applyGcrMutation.isPending}
            onClick={() => {
              applyGcrMutation.mutate(undefined, { onSuccess: () => setConfirmAction(null) });
            }}
          >
            Conferma
          </button>
        </div>
      </AppModal>

      <AppModal
        open={confirmAction === "railway"}
        onClose={() => setConfirmAction(null)}
        title="Ripristina da Railway"
      >
        <p className="gcr-card__description">
          Ripristinerai tutti i modelli del progetto ai default registry/env Railway. Gli override
          manuali verranno rimossi.
        </p>
        <div className="ai-model-settings-edit__actions">
          <button type="button" className="gcr-btn gcr-btn--secondary" onClick={() => setConfirmAction(null)}>
            Annulla
          </button>
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            disabled={resetRailwayMutation.isPending}
            onClick={() => {
              resetRailwayMutation.mutate(undefined, { onSuccess: () => setConfirmAction(null) });
            }}
          >
            Conferma
          </button>
        </div>
      </AppModal>
    </div>
  );
}
