import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  SeoCollectionDetailResponse,
  SeoProductDetailResponse,
  SeoProductMetafieldItem,
} from "@gcr/shared";
import { SeoEditModal } from "./SeoEditModal";
import { SeoFieldEditor } from "./SeoFieldEditor";
import { SeoMetafieldsEditor } from "./SeoMetafieldsEditor";
import { SeoProposalFooter } from "./SeoProposalFooter";
import { SeoScoreBadge } from "./SeoScoreBadge";
import {
  applyGlobalMergeToFieldState,
  applyFieldValueToForm,
  applyMetafieldValue,
  acceptFieldState,
  applyAiFieldState,
  buildApplyFieldsPayload,
  buildChangedProposalValues,
  collectChangedKeysFromMerge,
  commitFieldStateAsOriginal,
  formatApplicableFieldLabels,
  getApplicableFieldKeys,
  hasApplicableChanges,
  imageAltFieldKey,
  initFieldStateMap,
  markFieldsFromGlobalAi,
  metafieldFieldKey,
  restoreFieldOriginal,
  setFieldGenerating,
  updateFieldStateValue,
  type FieldStateMap,
  type SeoEditableField,
} from "./seoFieldState";
import {
  extractProposedValues,
  getEffectiveIssues,
  hasUsableProposalFields,
  mergeProposedIntoForm,
  needsImageAltWarning,
  normalizeFormValues,
  resolveMediaFromProposal,
} from "./seoFormValues";
import {
  useApplyEntityFields,
  useGenerateProposal,
  useGenerateProposalField,
  useSaveManualProposal,
  useSyncCollectionSeo,
  useSyncMetafieldDefinitions,
  useSyncProductSeo,
} from "../../../hooks/useContentSeo";

type DrawerTab = "main" | "metafields";

function buildMetafieldValues(metafields: SeoProductMetafieldItem[]): Record<string, string> {
  const map: Record<string, string> = {};
  for (const mf of metafields) {
    map[mf.id] = mf.displayValue ?? mf.value ?? "";
  }
  return map;
}

function normalizeReasoning(reasoning: unknown[] | null | undefined): string[] {
  if (!reasoning) return [];
  return reasoning.map((r) => (typeof r === "string" ? r : String(r)));
}

interface SeoEntityEditDrawerProps {
  open: boolean;
  onClose: () => void;
  projectId: string;
  entityType: "product" | "collection";
  entityId: string;
  title: string;
  productDetail?: SeoProductDetailResponse;
  collectionDetail?: SeoCollectionDetailResponse;
  detailLoading?: boolean;
  detailError?: boolean;
  detailErrorMessage?: string;
  openaiConfigured: boolean;
  writeProductsAvailable: boolean;
  onDetailRefresh?: () => void;
}

export function SeoEntityEditDrawer({
  open,
  onClose,
  projectId,
  entityType,
  entityId,
  title,
  productDetail,
  collectionDetail,
  detailLoading,
  detailError,
  detailErrorMessage,
  openaiConfigured,
  writeProductsAvailable,
  onDetailRefresh,
}: SeoEntityEditDrawerProps) {
  const [tab, setTab] = useState<DrawerTab>("main");
  const [formValues, setFormValues] = useState<Record<string, unknown>>({});
  const [mediaImages, setMediaImages] = useState<Record<string, unknown>[]>([]);
  const [metafields, setMetafields] = useState<SeoProductMetafieldItem[]>([]);
  const [metafieldValues, setMetafieldValues] = useState<Record<string, string>>({});
  const [formDirty, setFormDirty] = useState(false);
  const [appliedAt, setAppliedAt] = useState<string | null>(null);
  const [applyMessage, setApplyMessage] = useState<string | null>(null);
  const [localUpdateFailed, setLocalUpdateFailed] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [aiToast, setAiToast] = useState<string | null>(null);
  const [aiToastVariant, setAiToastVariant] = useState<"success" | "error" | "warn">("success");
  const [aiReasoning, setAiReasoning] = useState<string[]>([]);
  const [aiRiskLevel, setAiRiskLevel] = useState<string | null>(null);
  const [fieldStateMap, setFieldStateMap] = useState<FieldStateMap>({});
  const initialFormRef = useRef<string>("");
  const lastInitKeyRef = useRef<string | null>(null);

  const entityKey = `${entityType}:${entityId}`;
  const detail = entityType === "product" ? productDetail : collectionDetail;
  const analysis = detail?.analysis as Record<string, unknown> | null | undefined;
  const scoreBreakdown = detail?.scoreBreakdown;
  const issues = (analysis?.issues as Record<string, unknown>[] | undefined) ?? null;
  const effectiveIssues = useMemo(
    () => getEffectiveIssues(issues, formValues, mediaImages),
    [issues, formValues, mediaImages],
  );
  const scoreTotal = (analysis?.scoreTotal ?? analysis?.score_total) as number | undefined;
  const severity = (analysis?.severity as string | undefined) ?? undefined;

  const tabs: { id: DrawerTab; label: string }[] =
    entityType === "product"
      ? [
          { id: "main", label: "Principale" },
          { id: "metafields", label: "Metafield" },
        ]
      : [{ id: "main", label: "Principale" }];

  const saveManual = useSaveManualProposal(projectId);
  const applyFields = useApplyEntityFields(projectId);
  const generateAi = useGenerateProposal(projectId);
  const generateField = useGenerateProposalField(projectId);
  const syncProduct = useSyncProductSeo(projectId);
  const syncCollection = useSyncCollectionSeo(projectId);
  const syncDefinitions = useSyncMetafieldDefinitions(projectId);

  const initFormFromDetail = useCallback(
    (detailSource: SeoProductDetailResponse | SeoCollectionDetailResponse) => {
      const raw =
        detailSource.currentValues ??
        (detailSource as { current_values?: Record<string, unknown> }).current_values;
      const normalized = normalizeFormValues(raw, entityType, detailSource);
      const images =
        entityType === "product"
          ? (productDetail?.images ?? (normalized.images as Record<string, unknown>[]) ?? [])
          : collectionDetail?.image
            ? [collectionDetail.image]
            : [];
      const productMetafields =
        entityType === "product"
          ? ((detailSource as SeoProductDetailResponse).metafields ?? [])
          : [];
      const mfValues = buildMetafieldValues(productMetafields);
      setFormValues(normalized);
      initialFormRef.current = JSON.stringify({ form: normalized, metafields: mfValues });
      setFormDirty(false);
      setMediaImages(images);
      setMetafields(productMetafields);
      setMetafieldValues(mfValues);
      setFieldStateMap(initFieldStateMap(normalized, entityType, images, productMetafields, mfValues));
      setAiReasoning([]);
      setAiRiskLevel(null);
      setAiToast(null);
      setTab("main");
      setAppliedAt(null);
      setApplyMessage(null);
      setLocalUpdateFailed(false);
    },
    [entityType, productDetail?.images, collectionDetail?.image],
  );

  useEffect(() => {
    if (!open) {
      lastInitKeyRef.current = null;
      return;
    }
    if (!detail || formDirty) return;
    if (lastInitKeyRef.current === entityKey) return;
    initFormFromDetail(detail);
    lastInitKeyRef.current = entityKey;
  }, [open, entityKey, detail, formDirty, initFormFromDetail]);

  const markDirty = (nextForm: Record<string, unknown>, nextMf: Record<string, string>) => {
    const snapshot = JSON.stringify({ form: nextForm, metafields: nextMf });
    setFormDirty(snapshot !== initialFormRef.current);
  };

  const refreshFormFromValues = (
    values: Record<string, unknown> | null | undefined,
    detailSource?: SeoProductDetailResponse | SeoCollectionDetailResponse,
  ) => {
    if (!values) return;
    const normalized = normalizeFormValues(values, entityType, detailSource ?? detail);
    const images =
      entityType === "product" && Array.isArray(normalized.images)
        ? (normalized.images as Record<string, unknown>[])
        : mediaImages;
    const productMetafields =
      entityType === "product" && detailSource
        ? ((detailSource as SeoProductDetailResponse).metafields ?? metafields)
        : [];
    const mfValues = buildMetafieldValues(productMetafields);
    setFormValues(normalized);
    initialFormRef.current = JSON.stringify({ form: normalized, metafields: mfValues });
    setFormDirty(false);
    setMetafields(productMetafields);
    setMetafieldValues(mfValues);
    setFieldStateMap(initFieldStateMap(normalized, entityType, images, productMetafields, mfValues));
    setAiReasoning([]);
    setAiRiskLevel(null);
    if (entityType === "product" && Array.isArray(normalized.images)) {
      setMediaImages(normalized.images as Record<string, unknown>[]);
    }
  };

  const handleRestoreOriginal = () => {
    if (!detail) return;
    if (formDirty) {
      const ok = window.confirm("Ripristinare i valori originali da Shopify? Le modifiche non salvate andranno perse.");
      if (!ok) return;
    }
    initFormFromDetail(detail);
    lastInitKeyRef.current = entityKey;
  };

  const handleClose = () => {
    if (formDirty) {
      const ok = window.confirm("Hai modifiche non salvate. Chiudere comunque?");
      if (!ok) return;
    }
    onClose();
  };

  const handleFieldChange = (key: string, value: unknown) => {
    const strVal = String(value ?? "");
    setFormValues((prev) => {
      const next = { ...prev, [key]: value };
      markDirty(next, metafieldValues);
      return next;
    });
    setFieldStateMap((prev) => updateFieldStateValue(prev, key, strVal, "manual"));
  };

  const handleMetafieldChange = (metafieldId: string, value: string) => {
    const fk = metafieldFieldKey(metafieldId);
    setMetafieldValues((prev) => {
      const next = applyMetafieldValue(prev, metafieldId, value);
      markDirty(formValues, next);
      return next;
    });
    setFieldStateMap((prev) => updateFieldStateValue(prev, fk, value, "manual"));
  };

  const handleImageAltChange = (index: number, alt: string) => {
    setMediaImages((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], altText: alt };
      const imageId = String(next[index].id ?? index);
      const fk = imageAltFieldKey(imageId);
      setFieldStateMap((fsm) => updateFieldStateValue(fsm, fk, alt, "manual"));
      setFormValues((fv) => {
        const updated = { ...fv, images: next };
        markDirty(updated, metafieldValues);
        return updated;
      });
      return next;
    });
  };

  const handleRestoreField = (fieldKey: string) => {
    const restored = restoreFieldOriginal(fieldStateMap, fieldKey);
    const row = restored[fieldKey];
    if (!row) return;
    setFieldStateMap(restored);
    if (fieldKey.startsWith("imageAlt:")) {
      const imageId = fieldKey.slice("imageAlt:".length);
      setMediaImages((prev) =>
        prev.map((img) =>
          String(img.id ?? "") === imageId ? { ...img, altText: row.originalValue } : img,
        ),
      );
      setFormValues((fv) => {
        const images = (fv.images as Record<string, unknown>[] | undefined)?.map((img) =>
          String(img.id ?? "") === imageId ? { ...img, altText: row.originalValue } : img,
        );
        const next = { ...fv, images };
        markDirty(next, metafieldValues);
        return next;
      });
    } else if (fieldKey.startsWith("metafield:")) {
      const metafieldId = fieldKey.slice("metafield:".length);
      setMetafieldValues((prev) => {
        const next = applyMetafieldValue(prev, metafieldId, row.originalValue);
        markDirty(formValues, next);
        return next;
      });
    } else {
      setFormValues((prev) => {
        const next = { ...prev, [fieldKey]: row.originalValue };
        markDirty(next, metafieldValues);
        return next;
      });
    }
  };

  const handleAcceptField = (fieldKey: string) => {
    setFieldStateMap((prev) => acceptFieldState(prev, fieldKey));
  };

  const handleGenerateFieldAi = (field: SeoEditableField, imageId?: string) => {
    const stateKey =
      field === "imageAlt" && imageId ? imageAltFieldKey(imageId) : field;
    setFieldStateMap((prev) => setFieldGenerating(prev, stateKey));
    generateField.mutate(
      { entityType, entityId, field, imageId, useAi: true },
      {
        onSuccess: (res) => {
          const applied = applyFieldValueToForm(
            formValues,
            mediaImages,
            field,
            res.value,
            entityType,
          );
          setFormValues(applied.formValues);
          setMediaImages(applied.mediaImages);
          let strValue = "";
          if (field === "imageAlt" && entityType === "product" && imageId) {
            const img = applied.mediaImages.find((m) => String(m.id ?? "") === imageId);
            strValue = String(img?.altText ?? img?.alt ?? "");
          } else if (field === "imageAlt") {
            strValue = String(applied.formValues.imageAlt ?? "");
          } else {
            strValue = String(applied.formValues[field] ?? "");
          }
          setFieldStateMap((prev) =>
            applyAiFieldState(prev, stateKey, strValue, res.reasoning ?? undefined, res.riskLevel),
          );
          markDirty(applied.formValues, metafieldValues);
          setAiToastVariant("success");
          setAiToast(`Campo aggiornato con AI. Accetta il campo e applica le modifiche selezionate.`);
        },
        onError: () => {
          setFieldStateMap((prev) => {
            const row = prev[stateKey];
            if (!row) return prev;
            return { ...prev, [stateKey]: { ...row, generating: false } };
          });
          setAiToastVariant("error");
          setAiToast("Generazione AI del campo non riuscita.");
        },
      },
    );
  };

  const handleGenerateMetafieldAi = (mf: SeoProductMetafieldItem) => {
    const stateKey = metafieldFieldKey(mf.id);
    setFieldStateMap((prev) => setFieldGenerating(prev, stateKey));
    generateField.mutate(
      {
        entityType,
        entityId,
        field: "metafield",
        metafieldId: mf.metafieldId ?? null,
        definitionId: mf.definitionId,
        namespace: mf.namespace,
        key: mf.key,
        type: mf.type,
        useAi: true,
      },
      {
        onSuccess: (res) => {
          const strValue = String(res.value ?? "");
          setMetafieldValues((prev) => {
            const next = applyMetafieldValue(prev, mf.id, strValue);
            markDirty(formValues, next);
            return next;
          });
          setFieldStateMap((prev) =>
            applyAiFieldState(prev, stateKey, strValue, res.reasoning ?? undefined, res.riskLevel),
          );
          setAiToastVariant("success");
          setAiToast("Metafield aggiornato con AI. Accetta il campo e applica le modifiche selezionate.");
        },
        onError: () => {
          setFieldStateMap((prev) => {
            const row = prev[stateKey];
            if (!row) return prev;
            return { ...prev, [stateKey]: { ...row, generating: false } };
          });
          setAiToastVariant("error");
          setAiToast("Generazione AI del metafield non riuscita.");
        },
      },
    );
  };

  const handleSaveDraft = () => {
    const { proposedValues, changedFields } = buildChangedProposalValues(
      formValues,
      entityType,
      mediaImages,
      fieldStateMap,
      metafields,
    );
    if (changedFields.length === 0) {
      setAiToastVariant("warn");
      setAiToast("Nessuna modifica da salvare.");
      return;
    }
    saveManual.mutate(
      {
        entityType,
        entityId,
        proposedValues,
        changedFields,
      },
      {
        onSuccess: () => {
          initialFormRef.current = JSON.stringify({ form: formValues, metafields: metafieldValues });
          setFormDirty(false);
          setFieldStateMap(commitFieldStateAsOriginal(fieldStateMap));
          setAiToastVariant("success");
          setAiToast("Bozza salvata.");
          onDetailRefresh?.();
        },
      },
    );
  };

  const handleGenerateAi = () => {
    generateAi.mutate(
      {
        entityType,
        entityId,
        useAi: true,
        mode: "fill_missing_and_improve",
      },
      {
        onSuccess: (proposal) => {
          const proposed = extractProposedValues(proposal);
          const merged = mergeProposedIntoForm(formValues, proposed, entityType);
          let nextMedia = mediaImages;
          if (entityType === "product") {
            nextMedia = resolveMediaFromProposal(
              proposed,
              mediaImages.length > 0
                ? mediaImages
                : ((merged.images as Record<string, unknown>[]) ?? []),
            );
            setMediaImages(nextMedia);
          }
          const usable = hasUsableProposalFields(
            formValues,
            merged,
            entityType,
            mediaImages,
            nextMedia,
          );
          if (!usable) {
            setAiToastVariant("error");
            setAiToast("La proposta AI non contiene campi utilizzabili.");
            return;
          }
          setFormValues(merged);
          markDirty(merged, metafieldValues);
          const changed = collectChangedKeysFromMerge(
            formValues,
            merged,
            entityType,
            mediaImages,
            nextMedia,
          );
          setFieldStateMap((prev) =>
            markFieldsFromGlobalAi(
              applyGlobalMergeToFieldState(prev, merged, nextMedia, changed),
              changed,
              normalizeReasoning(proposal.reasoning)[0],
              proposal.riskLevel ?? undefined,
            ),
          );
          setAiReasoning(normalizeReasoning(proposal.reasoning));
          setAiRiskLevel(proposal.riskLevel ?? null);
          setTab("main");
          if (needsImageAltWarning(entityType, nextMedia, proposed)) {
            setAiToastVariant("warn");
            setAiToast(
              "La proposta AI non ha generato alt text per le immagini. Proposta AI inserita nei campi. Controlla, modifica se serve e salva come proposta.",
            );
          } else {
            setAiToastVariant("success");
            setAiToast(
              "Proposta AI inserita nei campi. Accetta i campi desiderati e applica le modifiche selezionate.",
            );
          }
        },
      },
    );
  };

  const handleApplySelectedFields = () => {
    const applicableKeys = getApplicableFieldKeys(fieldStateMap);
    if (applicableKeys.length === 0) {
      setAiToastVariant("warn");
      setAiToast("Nessuna modifica selezionata da applicare. Accetta i campi AI o modifica manualmente.");
      return;
    }
    const { fields, changedFields } = buildApplyFieldsPayload(
      formValues,
      entityType,
      mediaImages,
      fieldStateMap,
      metafields,
      metafieldValues,
    );
    if (changedFields.length === 0) {
      setAiToastVariant("warn");
      setAiToast("Nessuna modifica selezionata da applicare.");
      return;
    }
    const labels = formatApplicableFieldLabels(applicableKeys, entityType);
    const confirmed = window.confirm(
      `Stai applicando: ${labels.join(", ")}.\n\nConfermi di applicare su Shopify? Questa azione modifica il negozio live.`,
    );
    if (!confirmed) return;

    applyFields.mutate(
      { entityType, entityId, fields, changedFields },
      {
        onSuccess: (res) => {
          if (res.message && !res.applied) {
            alert(res.message);
            return;
          }
          if (res.applied) {
            setAppliedAt(new Date().toISOString());
            setApplyMessage(res.message ?? "Applicato su Shopify.");
            setLocalUpdateFailed(Boolean(res.localUpdateFailed));
            const detailPayload = res.detail as
              | SeoProductDetailResponse
              | SeoCollectionDetailResponse
              | undefined;
            if (detailPayload?.currentValues) {
              refreshFormFromValues(detailPayload.currentValues, detailPayload);
            } else if (res.updatedEntity) {
              refreshFormFromValues(res.updatedEntity, detailPayload);
            } else {
              setFieldStateMap(commitFieldStateAsOriginal(fieldStateMap));
              initialFormRef.current = JSON.stringify({ form: formValues, metafields: metafieldValues });
              setFormDirty(false);
            }
            setAiToastVariant("success");
            setAiToast(res.message ?? "Modifiche applicate su Shopify.");
          }
          onDetailRefresh?.();
        },
        onError: () => {
          setAiToastVariant("error");
          setAiToast("Applicazione su Shopify non riuscita.");
        },
      },
    );
  };

  const handleSyncFromShopify = () => {
    const mutation = entityType === "product" ? syncProduct : syncCollection;
    mutation.mutate(entityId, {
      onSuccess: (res) => {
        setSyncMessage(res.message);
        setLocalUpdateFailed(false);
        const detailPayload = res.detail as
          | SeoProductDetailResponse
          | SeoCollectionDetailResponse
          | undefined;
        if (detailPayload?.currentValues) {
          refreshFormFromValues(detailPayload.currentValues, detailPayload);
        }
        onDetailRefresh?.();
      },
    });
  };

  const syncLoading = syncProduct.isPending || syncCollection.isPending;

  const actionLoading =
    saveManual.isPending ||
    applyFields.isPending ||
    generateAi.isPending ||
    generateField.isPending ||
    syncLoading;

  const headerExtra = scoreTotal != null && (
    <SeoScoreBadge score={scoreTotal} severity={severity as never} />
  );

  const footer = (
    <SeoProposalFooter
      writeProductsAvailable={writeProductsAvailable}
      openaiConfigured={openaiConfigured}
      loading={actionLoading}
      saveLoading={saveManual.isPending}
      applyLoading={applyFields.isPending}
      generateLoading={generateAi.isPending}
      applyDisabled={!hasApplicableChanges(fieldStateMap)}
      saveDisabled={!hasApplicableChanges(fieldStateMap)}
      applyDisabledMessage={
        !hasApplicableChanges(fieldStateMap)
          ? "Nessuna modifica selezionata. Accetta i campi AI o modifica manualmente."
          : undefined
      }
      saveDisabledMessage={
        !hasApplicableChanges(fieldStateMap) ? "Nessuna modifica da salvare." : undefined
      }
      onApplySelected={handleApplySelectedFields}
      onSaveDraft={handleSaveDraft}
      onGenerateAi={handleGenerateAi}
      onCancel={handleClose}
    />
  );

  const aiBannerClass =
    aiToastVariant === "error"
      ? "content-seo-banner content-seo-banner--warn"
      : aiToastVariant === "warn"
        ? "content-seo-banner content-seo-banner--warn"
        : "content-seo-banner content-seo-banner--success";

  return (
    <SeoEditModal
      open={open}
      onClose={handleClose}
      title={title}
      headerExtra={headerExtra}
      footer={!detailLoading && detail ? footer : undefined}
    >
      {detailLoading && (
        <div className="seo-edit-drawer__skeleton" aria-busy="true">
          <div className="gcr-skeleton seo-skeleton-row" />
          <div className="gcr-skeleton seo-skeleton-row" />
          <div className="gcr-skeleton seo-skeleton-row" />
        </div>
      )}

      {!detailLoading && detailError && (
        <div className="seo-edit-drawer__error">
          <p className="seo-edit-drawer__error-message">
            {detailErrorMessage ?? "Impossibile caricare i dati SEO."}
          </p>
          {onDetailRefresh && (
            <button
              type="button"
              className="gcr-btn gcr-btn--primary"
              onClick={() => onDetailRefresh()}
            >
              Riprova
            </button>
          )}
        </div>
      )}

      {!detailLoading && !detailError && !detail && (
        <p className="shopify-empty-copy">Nessun dato disponibile per questa entità.</p>
      )}

      {!detailLoading && detail && (
        <>
          <div className="seo-edit-drawer__toolbar">
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              disabled={syncLoading || actionLoading}
              onClick={handleSyncFromShopify}
            >
              {syncLoading ? "Sincronizzazione…" : "Sincronizza da Shopify"}
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              disabled={actionLoading}
              onClick={handleRestoreOriginal}
            >
              Ripristina valori originali
            </button>
          </div>

          {appliedAt && (
            <div className="content-seo-banner content-seo-banner--success">
              Applicato su Shopify
              {applyMessage ? ` — ${applyMessage}` : ""}
              {appliedAt ? ` (${new Date(appliedAt).toLocaleString("it-IT")})` : ""}
            </div>
          )}

          {localUpdateFailed && (
            <div className="content-seo-banner content-seo-banner--warn">
              Aggiornamento locale non riuscito. Usa &quot;Sincronizza da Shopify&quot; per
              riallineare i dati.
            </div>
          )}

          {syncMessage && (
            <div className="content-seo-banner content-seo-banner--success">{syncMessage}</div>
          )}

          {aiToast && <div className={aiBannerClass}>{aiToast}</div>}

          <div className="seo-edit-drawer__tabs">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                className={`seo-edit-drawer__tab ${tab === t.id ? "seo-edit-drawer__tab--active" : ""}`}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === "main" && (
            <>
              <SeoFieldEditor
                entityType={entityType}
                values={formValues}
                issues={effectiveIssues}
                scoreBreakdown={scoreBreakdown}
                fieldStateMap={fieldStateMap}
                mediaImages={mediaImages}
                openaiConfigured={openaiConfigured}
                onChange={handleFieldChange}
                onImageAltChange={handleImageAltChange}
                onGenerateField={handleGenerateFieldAi}
                onRestoreField={handleRestoreField}
                onAcceptField={handleAcceptField}
              />
              {(aiReasoning.length > 0 || aiRiskLevel) && (
                <div className="gcr-card seo-ai-reasoning-card">
                  {aiRiskLevel && (
                    <p className="seo-ai-reasoning-card__risk">
                      Rischio proposta: <strong>{aiRiskLevel}</strong>
                    </p>
                  )}
                  {aiReasoning.length > 0 && (
                    <ul className="seo-ai-reasoning-card__list">
                      {aiReasoning.map((line, i) => (
                        <li key={i}>{line}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </>
          )}

          {tab === "metafields" && entityType === "product" && (
            <SeoMetafieldsEditor
              metafields={metafields}
              fieldStateMap={fieldStateMap}
              openaiConfigured={openaiConfigured}
              syncLoading={syncLoading}
              definitionsSyncLoading={syncDefinitions.isPending}
              hasDefinitions={productDetail?.hasMetafieldDefinitions}
              onMetafieldChange={handleMetafieldChange}
              onGenerateMetafield={handleGenerateMetafieldAi}
              onRestoreField={handleRestoreField}
              onAcceptField={handleAcceptField}
              onSyncMetafields={handleSyncFromShopify}
              onSyncDefinitions={() => {
                syncDefinitions.mutate(undefined, {
                  onSuccess: () => {
                    setSyncMessage("Definizioni metafield sincronizzate.");
                    onDetailRefresh?.();
                  },
                  onError: () => {
                    setSyncMessage("Sincronizzazione definizioni non riuscita.");
                  },
                });
              }}
            />
          )}
        </>
      )}
    </SeoEditModal>
  );
}
