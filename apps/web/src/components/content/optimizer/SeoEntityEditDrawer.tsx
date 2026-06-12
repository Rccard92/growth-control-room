import { useEffect, useMemo, useState } from "react";
import type {
  SeoCollectionDetailResponse,
  SeoOptimizationProposal,
  SeoProductDetailResponse,
} from "@gcr/shared";
import { SeoFieldEditor } from "./SeoFieldEditor";
import { SeoProposalActions } from "./SeoProposalActions";
import { SeoProposalPreview } from "./SeoProposalPreview";
import { SeoScoreBadge } from "./SeoScoreBadge";
import { SeoScoreBreakdown } from "./SeoScoreBreakdown";
import {
  useGenerateProposal,
  usePreviewProposal,
  useProposalActions,
  useSaveManualProposal,
} from "../../../hooks/useContentSeo";

type DrawerTab = "fields" | "score" | "images" | "proposal" | "history";

const TABS: { id: DrawerTab; label: string }[] = [
  { id: "fields", label: "Campi SEO" },
  { id: "score", label: "Score" },
  { id: "images", label: "Immagini" },
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
  openaiConfigured: boolean;
  writeProductsAvailable: boolean;
  onDetailRefresh?: () => void;
}

function mergeProposedIntoForm(
  current: Record<string, unknown>,
  proposed: Record<string, unknown> | null | undefined,
): Record<string, unknown> {
  if (!proposed) return { ...current };
  const merged = { ...current };
  for (const [key, val] of Object.entries(proposed)) {
    if (key === "reasoning" || key === "risk_level") continue;
    if (val !== undefined && val !== null) {
      merged[key] = val;
    }
  }
  return merged;
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
  openaiConfigured,
  writeProductsAvailable,
  onDetailRefresh,
}: SeoEntityEditDrawerProps) {
  const [tab, setTab] = useState<DrawerTab>("fields");
  const [formValues, setFormValues] = useState<Record<string, unknown>>({});
  const [activeProposalId, setActiveProposalId] = useState<string | null>(null);
  const [mediaImages, setMediaImages] = useState<Record<string, unknown>[]>([]);

  const detail = entityType === "product" ? productDetail : collectionDetail;
  const analysis = detail?.analysis as Record<string, unknown> | null | undefined;
  const scoreBreakdown = detail?.scoreBreakdown;
  const issues = (analysis?.issues as Record<string, unknown>[] | undefined) ?? null;
  const scoreTotal = (analysis?.scoreTotal ?? analysis?.score_total) as number | undefined;

  const saveManual = useSaveManualProposal(projectId);
  const generateAi = useGenerateProposal(projectId);
  const proposalActions = useProposalActions(projectId);
  const preview = usePreviewProposal(projectId, activeProposalId);

  useEffect(() => {
    if (!open || !detail) return;
    setFormValues({ ...detail.currentValues });
    setMediaImages(
      entityType === "product"
        ? (productDetail?.images ?? [])
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

  if (!open) return null;

  const handleFieldChange = (key: string, value: unknown) => {
    setFormValues((prev) => ({ ...prev, [key]: value }));
  };

  const handleImageAltChange = (index: number, alt: string) => {
    setMediaImages((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], altText: alt };
      if (entityType === "product") {
        setFormValues((fv) => ({ ...fv, media_images: next }));
      }
      return next;
    });
  };

  const buildProposedValues = (): Record<string, unknown> => {
    const proposed = { ...formValues };
    if (entityType === "product") {
      proposed.media_images = mediaImages;
    }
    return proposed;
  };

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
          setFormValues((prev) =>
            mergeProposedIntoForm(prev, proposal.proposedValues ?? undefined),
          );
          setTab("proposal");
          onDetailRefresh?.();
        },
      },
    );
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

  return (
    <div className="seo-drawer-backdrop" onClick={onClose} role="presentation">
      <aside
        className="seo-drawer seo-edit-drawer gcr-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Modifica SEO"
      >
        <header className="seo-drawer__header">
          <div>
            <p className="gcr-card__label">Modifica SEO</p>
            <h3>{title}</h3>
            {scoreTotal != null && (
              <SeoScoreBadge
                score={scoreTotal}
                severity={analysis?.severity as never}
              />
            )}
          </div>
          <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
            Chiudi
          </button>
        </header>

        {detailLoading ? (
          <div className="gcr-skeleton seo-skeleton-row" />
        ) : (
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
                onChange={handleFieldChange}
              />
            )}

            {tab === "score" && (
              <SeoScoreBreakdown scoreTotal={scoreTotal} scoreBreakdown={scoreBreakdown} />
            )}

            {tab === "images" && (
              <div className="seo-images-tab">
                {mediaImages.length === 0 ? (
                  <p className="shopify-empty-copy">Nessuna immagine sincronizzata.</p>
                ) : (
                  mediaImages.map((img, idx) => (
                    <div key={idx} className="seo-images-tab__item">
                      {typeof img.url === "string" && (
                        <img src={img.url} alt="" className="seo-images-tab__thumb" />
                      )}
                      <label className="seo-field-editor__field">
                        <span className="seo-field-editor__label">Alt text</span>
                        <input
                          className="seo-field-editor__input"
                          type="text"
                          value={String(img.altText ?? img.alt ?? "")}
                          onChange={(e) => handleImageAltChange(idx, e.target.value)}
                        />
                      </label>
                    </div>
                  ))
                )}
              </div>
            )}

            {tab === "proposal" && (
              <>
                <SeoProposalPreview
                  preview={preview.data}
                  loading={preview.isLoading && Boolean(activeProposalId)}
                />
                <SeoProposalActions
                  proposal={activeProposal}
                  writeProductsAvailable={writeProductsAvailable}
                  loading={actionLoading}
                  onSaveDraft={handleSaveDraft}
                  onGenerateAi={handleGenerateAi}
                  aiDisabled={!openaiConfigured}
                  aiTooltip={
                    openaiConfigured
                      ? undefined
                      : "Configura OPENAI_API_KEY per generare proposte automatiche."
                  }
                  saveLoading={saveManual.isPending}
                  generateLoading={generateAi.isPending}
                  onApprove={() => {
                    if (activeProposalId) {
                      proposalActions.approve.mutate(activeProposalId, {
                        onSuccess: onDetailRefresh,
                      });
                    }
                  }}
                  onReject={() => {
                    if (activeProposalId) {
                      proposalActions.reject.mutate(activeProposalId, {
                        onSuccess: onDetailRefresh,
                      });
                    }
                  }}
                  onApply={handleApply}
                />
              </>
            )}

            {tab === "history" && (
              <div className="seo-history-tab">
                <h4>Proposte</h4>
                {(detail?.proposalHistory ?? []).length === 0 ? (
                  <p className="shopify-empty-copy">Nessuna proposta precedente.</p>
                ) : (
                  <ul className="shopify-seo-list">
                    {(detail?.proposalHistory ?? []).map((p) => (
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
                {(detail?.changeLogs ?? []).length === 0 ? (
                  <p className="shopify-empty-copy">Nessuna modifica applicata.</p>
                ) : (
                  <ul className="shopify-seo-list">
                    {(detail?.changeLogs ?? []).map((log) => (
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
      </aside>
    </div>
  );
}
