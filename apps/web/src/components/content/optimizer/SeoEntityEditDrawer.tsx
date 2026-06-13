import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  SeoCollectionDetailResponse,
  SeoProductDetailResponse,
  SeoProductMetafieldItem,
  SeoProposalGenerateFieldResponse,
} from "@gcr/shared";
import { SeoEditModal } from "./SeoEditModal";
import { SeoFieldEditor } from "./SeoFieldEditor";
import { SeoMetafieldsEditor } from "./SeoMetafieldsEditor";
import { SeoProposalFooter } from "./SeoProposalFooter";
import { SeoScoreBadge } from "./SeoScoreBadge";
import {
  applyFieldValueToForm,
  applyMetafieldValue,
  acceptFieldState,
  applyAiFieldState,
  buildApplyFieldsPayload,
  buildChangedProposalValues,
  commitFieldStateAsOriginal,
  formatApplicableFieldLabels,
  getApplicableFieldKeys,
  hasApplicableChanges,
  imageAltFieldKey,
  initFieldStateMap,
  metafieldFieldKey,
  parseImageAltFieldKey,
  restoreFieldOriginal,
  setFieldAiSkipped,
  setFieldGenerating,
  clearFieldGenerating,
  updateFieldStateValue,
  type FieldStateMap,
  type SeoEditableField,
} from "./seoFieldState";
import {
  getEffectiveIssues,
  normalizeFormValues,
} from "./seoFormValues";
import {
  useApplyEntityFields,
  useSaveManualProposal,
  useSyncCollectionSeo,
  useSyncMetafieldDefinitions,
  useSyncProductSeo,
} from "../../../hooks/useContentSeo";
import { useSeoAiQueue } from "../../../hooks/useSeoAiQueue";
import { generateProposalField } from "../../../lib/content-api";

type DrawerTab = "main" | "metafields";

function buildMetafieldValues(metafields: SeoProductMetafieldItem[]): Record<string, string> {
  const map: Record<string, string> = {};
  for (const mf of metafields) {
    map[mf.id] = mf.displayValue ?? mf.value ?? "";
  }
  return map;
}

function countMissingAlts(mediaImages: Record<string, unknown>[]): number {
  return mediaImages.filter((img) => !String(img.altText ?? img.alt ?? "").trim()).length;
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
  const [applyError, setApplyError] = useState<string | null>(null);
  const [fieldStateMap, setFieldStateMap] = useState<FieldStateMap>({});
  const initialFormRef = useRef<string>("");
  const lastInitKeyRef = useRef<string | null>(null);

  const formValuesRef = useRef(formValues);
  const mediaImagesRef = useRef(mediaImages);
  const metafieldValuesRef = useRef(metafieldValues);
  const fieldStateMapRef = useRef(fieldStateMap);

  useEffect(() => {
    formValuesRef.current = formValues;
  }, [formValues]);
  useEffect(() => {
    mediaImagesRef.current = mediaImages;
  }, [mediaImages]);
  useEffect(() => {
    metafieldValuesRef.current = metafieldValues;
  }, [metafieldValues]);
  useEffect(() => {
    fieldStateMapRef.current = fieldStateMap;
  }, [fieldStateMap]);

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
  const syncProduct = useSyncProductSeo(projectId);
  const syncCollection = useSyncCollectionSeo(projectId);
  const syncDefinitions = useSyncMetafieldDefinitions(projectId);

  const markDirty = useCallback((nextForm: Record<string, unknown>, nextMf: Record<string, string>) => {
    const snapshot = JSON.stringify({ form: nextForm, metafields: nextMf });
    setFormDirty(snapshot !== initialFormRef.current);
  }, []);

  const applyAiResult = useCallback(
    (fieldKey: string, res: SeoProposalGenerateFieldResponse) => {
      if (fieldKey.startsWith("metafield:")) {
        const metafieldId = fieldKey.slice("metafield:".length);
        const strValue = String(res.value ?? "");
        const nextMf = applyMetafieldValue(metafieldValuesRef.current, metafieldId, strValue);
        setMetafieldValues(nextMf);
        markDirty(formValuesRef.current, nextMf);
        setFieldStateMap((prev) =>
          applyAiFieldState(prev, fieldKey, strValue, res.reasoning ?? undefined, res.riskLevel),
        );
        return;
      }

      let field: SeoEditableField;
      let imageId: string | undefined;
      if (fieldKey.startsWith("imageAlt:")) {
        field = "imageAlt";
        imageId = parseImageAltFieldKey(fieldKey) ?? undefined;
      } else {
        field = fieldKey as SeoEditableField;
      }

      const applied = applyFieldValueToForm(
        formValuesRef.current,
        mediaImagesRef.current,
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
        applyAiFieldState(prev, fieldKey, strValue, res.reasoning ?? undefined, res.riskLevel),
      );
      markDirty(applied.formValues, metafieldValuesRef.current);
    },
    [entityType, markDirty],
  );

  const aiQueue = useSeoAiQueue({
    onStartGenerating: (fieldKey) => {
      setFieldStateMap((prev) => setFieldGenerating(prev, fieldKey));
    },
    onClearGenerating: (fieldKey) => {
      setFieldStateMap((prev) => clearFieldGenerating(prev, fieldKey));
    },
    onApplyResult: applyAiResult,
    onSkipped: (fieldKey, message) => {
      setFieldStateMap((prev) => setFieldAiSkipped(prev, fieldKey, message));
    },
    onError: (fieldKey, message) => {
      setFieldStateMap((prev) => setFieldAiSkipped(prev, fieldKey, message));
    },
    getFieldState: (fieldKey) => {
      const row = fieldStateMapRef.current[fieldKey];
      return row ? { value: row.value, source: row.source } : undefined;
    },
  });

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
      setTab("main");
      setAppliedAt(null);
      setApplyMessage(null);
      setLocalUpdateFailed(false);
      setApplyError(null);
    },
    [entityType, productDetail?.images, collectionDetail?.image],
  );

  useEffect(() => {
    if (!open) {
      lastInitKeyRef.current = null;
      aiQueue.clear();
      return;
    }
    if (!detail || formDirty) return;
    if (lastInitKeyRef.current === entityKey) return;
    initFormFromDetail(detail);
    lastInitKeyRef.current = entityKey;
    // eslint-disable-next-line react-hooks/exhaustive-deps -- clear only on close
  }, [open, entityKey, detail, formDirty, initFormFromDetail]);

  useEffect(() => {
    if (!syncMessage) return;
    const timer = window.setTimeout(() => setSyncMessage(null), 5500);
    return () => window.clearTimeout(timer);
  }, [syncMessage]);

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
    if (entityType === "product" && Array.isArray(normalized.images)) {
      setMediaImages(normalized.images as Record<string, unknown>[]);
    }
  };

  const handleRestoreOriginal = () => {
    if (!detail) return;
    if (formDirty) {
      const ok = window.confirm(
        "Ripristinare i valori originali da Shopify? Le modifiche non salvate andranno perse.",
      );
      if (!ok) return;
    }
    aiQueue.clear();
    initFormFromDetail(detail);
    lastInitKeyRef.current = entityKey;
  };

  const handleClose = () => {
    if (formDirty) {
      const ok = window.confirm("Hai modifiche non salvate. Chiudere comunque?");
      if (!ok) return;
    }
    aiQueue.clear();
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

  const enqueueFieldAi = (field: SeoEditableField, imageId?: string) => {
    const stateKey = field === "imageAlt" && imageId ? imageAltFieldKey(imageId) : field;
    const row = fieldStateMapRef.current[stateKey];
    aiQueue.enqueue({
      fieldKey: stateKey,
      valueAtEnqueue: row?.value ?? "",
      sourceAtEnqueue: row?.source ?? "original",
      run: () =>
        generateProposalField(projectId, entityType, entityId, {
          field,
          imageId,
          useAi: true,
        }),
    });
  };

  const enqueueMetafieldAi = (mf: SeoProductMetafieldItem) => {
    const stateKey = metafieldFieldKey(mf.id);
    const row = fieldStateMapRef.current[stateKey];
    aiQueue.enqueue({
      fieldKey: stateKey,
      valueAtEnqueue: row?.value ?? "",
      sourceAtEnqueue: row?.source ?? "original",
      run: () =>
        generateProposalField(projectId, entityType, entityId, {
          field: "metafield",
          metafieldId: mf.metafieldId ?? null,
          definitionId: mf.definitionId,
          namespace: mf.namespace,
          key: mf.key,
          type: mf.type,
          useAi: true,
        }),
    });
  };

  const handleGenerateMissingAlts = () => {
    mediaImagesRef.current.forEach((img, idx) => {
      const alt = String(img.altText ?? img.alt ?? "").trim();
      if (alt) return;
      const imageId = String(img.id ?? idx);
      enqueueFieldAi("imageAlt", imageId);
    });
  };

  const handleSaveDraft = () => {
    const { proposedValues, changedFields } = buildChangedProposalValues(
      formValues,
      entityType,
      mediaImages,
      fieldStateMap,
      metafields,
    );
    if (changedFields.length === 0) return;

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
          onDetailRefresh?.();
        },
      },
    );
  };

  const handleApplySelectedFields = () => {
    const applicableKeys = getApplicableFieldKeys(fieldStateMap);
    if (applicableKeys.length === 0) return;

    const { fields, changedFields } = buildApplyFieldsPayload(
      formValues,
      entityType,
      mediaImages,
      fieldStateMap,
      metafields,
      metafieldValues,
    );
    if (changedFields.length === 0) return;

    const labels = formatApplicableFieldLabels(applicableKeys, entityType);
    const confirmed = window.confirm(
      `Stai applicando: ${labels.join(", ")}.\n\nConfermi di applicare su Shopify? Questa azione modifica il negozio live.`,
    );
    if (!confirmed) return;

    setApplyError(null);
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
          }
          onDetailRefresh?.();
        },
        onError: () => {
          setApplyError("Applicazione su Shopify non riuscita.");
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

  const actionLoading = saveManual.isPending || applyFields.isPending || syncLoading;

  const missingAltCount = useMemo(
    () => (entityType === "product" ? countMissingAlts(mediaImages) : 0),
    [entityType, mediaImages],
  );

  const batchAltLoading = useMemo(
    () =>
      mediaImages.some((img, idx) => {
        const fk = imageAltFieldKey(String(img.id ?? idx));
        return fieldStateMap[fk]?.generating;
      }),
    [mediaImages, fieldStateMap],
  );

  const headerExtra = scoreTotal != null && (
    <SeoScoreBadge score={scoreTotal} severity={severity as never} />
  );

  const headerActions = (
    <>
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
        disabled={actionLoading || aiQueue.isProcessing}
        onClick={handleRestoreOriginal}
      >
        Ripristina valori originali
      </button>
    </>
  );

  const headerStatus = syncMessage ? (
    <span className="seo-edit-modal__sync-status">{syncMessage}</span>
  ) : null;

  const footer = (
    <SeoProposalFooter
      writeProductsAvailable={writeProductsAvailable}
      openaiConfigured={openaiConfigured}
      loading={actionLoading}
      saveLoading={saveManual.isPending}
      applyLoading={applyFields.isPending}
      applyDisabled={!hasApplicableChanges(fieldStateMap)}
      saveDisabled={!hasApplicableChanges(fieldStateMap)}
      onApplySelected={handleApplySelectedFields}
      onSaveDraft={handleSaveDraft}
      onCancel={handleClose}
    />
  );

  return (
    <SeoEditModal
      open={open}
      onClose={handleClose}
      title={title}
      headerExtra={headerExtra}
      headerActions={headerActions}
      headerStatus={headerStatus}
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

          {applyError && (
            <div className="content-seo-banner content-seo-banner--warn">{applyError}</div>
          )}

          <div className="seo-edit-drawer__tabs" role="tablist" aria-label="Sezioni modifica SEO">
            {tabs.map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={tab === t.id}
                className={`seo-edit-drawer__tab ${tab === t.id ? "seo-edit-drawer__tab--active" : ""}`}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === "main" && (
            <SeoFieldEditor
              entityType={entityType}
              values={formValues}
              issues={effectiveIssues}
              scoreBreakdown={scoreBreakdown}
              fieldStateMap={fieldStateMap}
              mediaImages={mediaImages}
              openaiConfigured={openaiConfigured}
              missingAltCount={missingAltCount}
              batchAltLoading={batchAltLoading}
              onChange={handleFieldChange}
              onImageAltChange={handleImageAltChange}
              onGenerateField={enqueueFieldAi}
              onGenerateMissingAlts={handleGenerateMissingAlts}
              onRestoreField={handleRestoreField}
              onAcceptField={handleAcceptField}
            />
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
              onGenerateMetafield={enqueueMetafieldAi}
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
