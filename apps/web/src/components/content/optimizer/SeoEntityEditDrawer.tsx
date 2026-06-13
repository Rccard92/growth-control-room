import { useEffect, useMemo, useRef, useState } from "react";
import type {
  SeoCollectionDetailResponse,
  SeoOptimizationProposal,
  SeoProductDetailResponse,
} from "@gcr/shared";
import { SeoEditModal } from "./SeoEditModal";
import { SeoFieldEditor } from "./SeoFieldEditor";
import { SeoProposalFooter } from "./SeoProposalFooter";
import { SeoProposalPreview } from "./SeoProposalPreview";
import { SeoScoreBadge } from "./SeoScoreBadge";
import { SeoScoreBreakdown } from "./SeoScoreBreakdown";
import { SeoSkillAppliedPanel } from "./SeoSkillAppliedPanel";
import {
  mergeProposedIntoForm,
  normalizeFormValues,
  toProposalValues,
} from "./seoFormValues";
import {
  useGenerateProposal,
  usePreviewProposal,
  useProposalActions,
  useSaveManualProposal,
} from "../../../hooks/useContentSeo";

type DrawerTab = "fields" | "score" | "proposal" | "history";

const TABS: { id: DrawerTab; label: string }[] = [
  { id: "fields", label: "Campi SEO" },
  { id: "score", label: "Score" },
  { id: "proposal", label: "Proposta" },
  { id: "history", label: "Storico" },
];

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
  const [tab, setTab] = useState<DrawerTab>("fields");
  const [formValues, setFormValues] = useState<Record<string, unknown>>({});
  const [activeProposalId, setActiveProposalId] = useState<string | null>(null);
  const [mediaImages, setMediaImages] = useState<Record<string, unknown>[]>([]);
  const [formDirty, setFormDirty] = useState(false);
  const initialFormRef = useRef<string>("");

  const detail = entityType === "product" ? productDetail : collectionDetail;
  const analysis = detail?.analysis as Record<string, unknown> | null | undefined;
  const scoreBreakdown = detail?.scoreBreakdown;
  const issues = (analysis?.issues as Record<string, unknown>[] | undefined) ?? null;
  const scoreTotal = (analysis?.scoreTotal ?? analysis?.score_total) as number | undefined;
  const severity = (analysis?.severity as string | undefined) ?? undefined;

  const saveManual = useSaveManualProposal(projectId);
  const generateAi = useGenerateProposal(projectId);
  const proposalActions = useProposalActions(projectId);
  const preview = usePreviewProposal(projectId, activeProposalId);

  useEffect(() => {
    if (!open || !detail) return;
    const raw =
      detail.currentValues ??
      (detail as { current_values?: Record<string, unknown> }).current_values;
    const normalized = normalizeFormValues(raw, entityType, detail);
    setFormValues(normalized);
    initialFormRef.current = JSON.stringify(normalized);
    setFormDirty(false);
    setMediaImages(
      entityType === "product"
        ? (productDetail?.images ?? (normalized.images as Record<string, unknown>[]) ?? [])
        : collectionDetail?.image
          ? [collectionDetail.image]
          : [],
    );
    setActiveProposalId(detail.latestProposal?.id ?? null);
    setTab("fields");
  }, [open, detail, entityType, productDetail, collectionDetail]);

  const activeProposal: SeoOptimizationProposal | null | undefined = useMemo(() => {
    if (preview.data) {
      return {
        id: preview.data.proposalId,
        entityType: preview.data.entityType,
        entityId: preview.data.entityId,
        entityGid: "",
        status: preview.data.status,
        source: preview.data.source,
        riskLevel: preview.data.riskLevel,
        currentValues: preview.data.currentValues,
        proposedValues: preview.data.proposedValues,
        reasoning: preview.data.reasoning,
      };
    }
    return detail?.latestProposal;
  }, [detail?.latestProposal, preview.data]);

  const handleClose = () => {
    if (formDirty) {
      const ok = window.confirm("Hai modifiche non salvate. Chiudere comunque?");
      if (!ok) return;
    }
    onClose();
  };

  const handleFieldChange = (key: string, value: unknown) => {
    setFormValues((prev) => {
      const next = { ...prev, [key]: value };
      setFormDirty(JSON.stringify(next) !== initialFormRef.current);
      return next;
    });
  };

  const handleImageAltChange = (index: number, alt: string) => {
    setMediaImages((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], altText: alt };
      setFormValues((fv) => {
        const updated = { ...fv, images: next };
        setFormDirty(JSON.stringify(updated) !== initialFormRef.current);
        return updated;
      });
      return next;
    });
  };

  const buildProposedValues = () =>
    toProposalValues(formValues, entityType, mediaImages);

  const handleSaveDraft = () => {
    saveManual.mutate(
      {
        entityType,
        entityId,
        proposedValues: buildProposedValues(),
      },
      {
        onSuccess: (proposal) => {
          setActiveProposalId(proposal.id);
          initialFormRef.current = JSON.stringify(formValues);
          setFormDirty(false);
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
          setActiveProposalId(proposal.id);
          setTab("proposal");
          onDetailRefresh?.();
        },
      },
    );
  };

  const handleCopyProposalToForm = () => {
    const proposed = activeProposal?.proposedValues ?? preview.data?.proposedValues;
    if (!proposed) return;
    const merged = mergeProposedIntoForm(formValues, proposed, entityType);
    setFormValues(merged);
    if (entityType === "product" && Array.isArray(merged.images)) {
      setMediaImages(merged.images as Record<string, unknown>[]);
    }
    setFormDirty(JSON.stringify(merged) !== initialFormRef.current);
    setTab("fields");
  };

  const handleApply = () => {
    if (!activeProposalId) return;
    const confirmed = window.confirm(
      "Confermi di applicare le modifiche approvate su Shopify? Questa azione modifica il negozio live.",
    );
    if (!confirmed) return;
    proposalActions.apply.mutate(activeProposalId, {
      onSuccess: (res) => {
        if (res.message && !res.applied) {
          alert(res.message);
        }
        onDetailRefresh?.();
      },
    });
  };

  const actionLoading =
    saveManual.isPending ||
    generateAi.isPending ||
    proposalActions.approve.isPending ||
    proposalActions.reject.isPending ||
    proposalActions.apply.isPending;

  const headerExtra = scoreTotal != null && (
    <SeoScoreBadge score={scoreTotal} severity={severity as never} />
  );

  const footer = (
    <SeoProposalFooter
      proposal={activeProposal}
      writeProductsAvailable={writeProductsAvailable}
      openaiConfigured={openaiConfigured}
      loading={actionLoading}
      saveLoading={saveManual.isPending}
      generateLoading={generateAi.isPending}
      onSaveDraft={handleSaveDraft}
      onGenerateAi={handleGenerateAi}
      onApprove={() => {
        if (activeProposalId) {
          proposalActions.approve.mutate(activeProposalId, { onSuccess: onDetailRefresh });
        }
      }}
      onReject={() => {
        if (activeProposalId) {
          proposalActions.reject.mutate(activeProposalId, { onSuccess: onDetailRefresh });
        }
      }}
      onApply={handleApply}
      onCancel={handleClose}
    />
  );

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
          {entityType === "product" && productDetail && (
            <p className="seo-edit-drawer__meta">
              Vendite: {productDetail.quantitySold} · Stock: {productDetail.stock ?? "—"} ·
              Revenue: {productDetail.revenue.toFixed(2)}
            </p>
          )}

          <div className="seo-edit-drawer__tabs">
            {TABS.map((t) => (
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

          {tab === "fields" && (
            <SeoFieldEditor
              entityType={entityType}
              values={formValues}
              issues={issues}
              scoreBreakdown={scoreBreakdown}
              mediaImages={mediaImages}
              onChange={handleFieldChange}
              onImageAltChange={handleImageAltChange}
            />
          )}

          {tab === "score" && (
            <>
              <SeoSkillAppliedPanel skillMeta={detail.skillMeta} />
              <SeoScoreBreakdown
                scoreTotal={scoreTotal}
                scoreBreakdown={scoreBreakdown}
                skillMeta={detail.skillMeta}
              />
            </>
          )}

          {tab === "proposal" && (
            <>
              <SeoProposalPreview
                preview={preview.data}
                loading={preview.isLoading && Boolean(activeProposalId)}
              />
              {(activeProposal?.proposedValues || preview.data?.proposedValues) && (
                <button
                  type="button"
                  className="gcr-btn gcr-btn--secondary seo-copy-proposal-btn"
                  onClick={handleCopyProposalToForm}
                >
                  Copia proposta nel form
                </button>
              )}
            </>
          )}

          {tab === "history" && (
            <div className="seo-history-tab">
              <h4>Proposte</h4>
              {(detail.proposalHistory ?? []).length === 0 ? (
                <p className="shopify-empty-copy">Nessuna proposta precedente.</p>
              ) : (
                <ul className="shopify-seo-list">
                  {(detail.proposalHistory ?? []).map((p) => (
                    <li key={p.id} className="shopify-seo-list__item">
                      <span>
                        {p.status} · {p.source} · {p.riskLevel}
                      </span>
                      <button
                        type="button"
                        className="gcr-btn gcr-btn--secondary gcr-btn--sm"
                        onClick={() => {
                          setActiveProposalId(p.id);
                          setTab("proposal");
                        }}
                      >
                        Apri
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              <h4>Change log</h4>
              {(detail.changeLogs ?? []).length === 0 ? (
                <p className="shopify-empty-copy">Nessuna modifica applicata.</p>
              ) : (
                <ul className="shopify-seo-list">
                  {(detail.changeLogs ?? []).map((log) => (
                    <li key={log.id} className="shopify-seo-list__item">
                      <span>
                        {log.status}
                        {log.errorMessage ? ` · ${log.errorMessage}` : ""}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </>
      )}
    </SeoEditModal>
  );
}
