import type { ContentSeoEditorialItem, EditorialAiGenerationInfo } from "@gcr/shared";
import { useEditorialItemAiUsage } from "../../../hooks/useContentSeoEditorial";
import {
  articleSnapshotFromItem,
  briefSnapshotFromItem,
  formatAiCost,
  formatAiDate,
  pickAiInfo,
} from "./editorial-ai-utils";

interface EditorialAiGenerationAccordionProps {
  projectId: string;
  item: ContentSeoEditorialItem;
  variant: "brief" | "article" | "both";
}

function AiInfoSection({
  title,
  info,
}: {
  title: string;
  info: EditorialAiGenerationInfo | null;
}) {
  if (!info || !info.generated) {
    return (
      <div className="editorial-ai-info__section">
        <h6 className="editorial-ai-info__section-title">{title}</h6>
        <p className="editorial-ai-info__empty">Non generato</p>
      </div>
    );
  }

  return (
    <div className="editorial-ai-info__section">
      <h6 className="editorial-ai-info__section-title">{title}</h6>
      <ul className="editorial-ai-info__list">
        <li>
          <strong>Modello:</strong> {info.model ?? "—"}
        </li>
        <li>
          <strong>Costo stimato:</strong> {formatAiCost(info.estimatedTotalCost)}
        </li>
        <li>
          <strong>Generato il:</strong> {formatAiDate(info.createdAt)}
        </li>
        <li>
          <strong>Profilo:</strong> {info.contextProfile ?? "—"}
        </li>
        {info.status && info.status !== "success" && (
          <li>
            <strong>Stato:</strong> {info.status}
            {info.errorMessage ? ` — ${info.errorMessage}` : ""}
          </li>
        )}
      </ul>
      <details className="editorial-ai-info__details">
        <summary>Dettagli tecnici</summary>
        <ul className="editorial-ai-info__list editorial-ai-info__list--technical">
          <li>
            <strong>operation_key:</strong> {info.operationKey ?? "—"}
          </li>
          <li>
            <strong>Token input/output:</strong> {info.inputTokens ?? "—"} /{" "}
            {info.outputTokens ?? "—"}
          </li>
          <li>
            <strong>log id:</strong> {info.logId ?? "—"}
          </li>
          <li>
            <strong>context hash:</strong> {info.contextHash ?? "—"}
          </li>
          <li>
            <strong>prompt hash:</strong> {info.promptHash ?? "—"}
          </li>
          <li>
            <strong>status:</strong> {info.status ?? "—"}
          </li>
          {info.generatorVersion ? (
            <li>
              <strong>generator version:</strong> {info.generatorVersion}
            </li>
          ) : null}
        </ul>
      </details>
    </div>
  );
}

export function EditorialAiGenerationAccordion({
  projectId,
  item,
  variant,
}: EditorialAiGenerationAccordionProps) {
  const usageQuery = useEditorialItemAiUsage(projectId, item.id);

  const briefInfo = pickAiInfo(usageQuery.data?.brief, briefSnapshotFromItem(item));
  const articleInfo = pickAiInfo(usageQuery.data?.article, articleSnapshotFromItem(item));

  const showBrief = variant === "brief" || variant === "both";
  const showArticle = variant === "article" || variant === "both";

  return (
    <details className="editorial-ai-info gcr-card">
      <summary className="editorial-ai-info__summary">Info generazione AI</summary>
      <div className="editorial-ai-info__body">
        {usageQuery.isLoading && (
          <p className="editorial-ai-info__hint">Caricamento info AI…</p>
        )}
        {usageQuery.isError && (
          <p className="editorial-ai-info__hint">
            Log AI non disponibili — mostro snapshot salvato nel payload se presente.
          </p>
        )}
        {showBrief && <AiInfoSection title="Brief SEO" info={briefInfo} />}
        {showArticle && <AiInfoSection title="Articolo" info={articleInfo} />}
      </div>
    </details>
  );
}
