import type { EditorialArticlePayload, EditorialImagePayload } from "@gcr/shared";
import { buildEditorialImagePreviewUrl } from "../../../lib/content-api";
import {
  canApproveImage,
  FILENAME_STALE_MESSAGE,
  formatImageCost,
  formatImageFinalSize,
  formatImageProviderSize,
  formatImageUpdatedAt,
  getImageStatusLabel,
  getImageSyncLabel,
  hasGeneratedImage,
  hasShopifyCdnUrl,
  IMAGE_POST_PROCESSING_LABEL,
  IMAGE_STALE_MESSAGE,
  isImageFilenameStale,
  resolveImageStorageWarning,
  SHOPIFY_SCOPE_MISSING_WARNING,
} from "./editorial-image-utils";

interface EditorialImageTabProps {
  projectId: string;
  itemId: string;
  hasArticle: boolean;
  article: EditorialArticlePayload | null;
  image: EditorialImagePayload;
  imageIsStale: boolean;
  revisionNote: string;
  onRevisionNoteChange: (value: string) => void;
  onGenerate: () => void;
  onRegenerate: () => void;
  onApplyEdit: () => void;
  onApprove: () => void;
  onRemove: () => void;
  onSyncFromTitle?: () => void;
  onRetryUpload?: () => void;
  canWriteFiles?: boolean;
  shopifyConnected?: boolean;
  generateLoading?: boolean;
  editLoading?: boolean;
  approveLoading?: boolean;
  removeLoading?: boolean;
  syncLoading?: boolean;
  retryUploadLoading?: boolean;
}

export function EditorialImageTab({
  projectId,
  itemId,
  hasArticle,
  article,
  image,
  imageIsStale,
  revisionNote,
  onRevisionNoteChange,
  onGenerate,
  onRegenerate,
  onApplyEdit,
  onApprove,
  onRemove,
  onSyncFromTitle,
  onRetryUpload,
  canWriteFiles,
  shopifyConnected,
  generateLoading = false,
  editLoading = false,
  approveLoading = false,
  removeLoading = false,
  syncLoading = false,
  retryUploadLoading = false,
}: EditorialImageTabProps) {
  const previewUrl = buildEditorialImagePreviewUrl(projectId, itemId, image);
  const busy =
    generateLoading ||
    editLoading ||
    approveLoading ||
    removeLoading ||
    syncLoading ||
    retryUploadLoading;
  const altText = image.imageAlt ?? article?.title ?? "—";
  const filenameStale = article ? isImageFilenameStale(image, article.title) : false;
  const storageWarning = resolveImageStorageWarning(image, { canWriteFiles, shopifyConnected });
  const approveAllowed = canApproveImage(image);
  const showRetryUpload =
    Boolean(onRetryUpload) &&
    (image.imageStatus === "upload_error" ||
      (image.imageStatus === "generated" && !image.shopifyImageReady));

  if (!hasArticle || !article) {
    return (
      <div className="editorial-image-tab editorial-image-tab--empty">
        <p>Genera prima l&apos;articolo per creare l&apos;immagine hero.</p>
      </div>
    );
  }

  return (
    <div className="editorial-image-tab">
      <header className="editorial-image-tab__header">
        <div>
          <h3>Immagine hero</h3>
          <p className="editorial-image-tab__subtitle">
            Formato fisso 1200×800 JPG (3:2). Filename SEO e ALT sincronizzati al titolo articolo.
            Storage Shopify Files con URL CDN per la pubblicazione.
          </p>
        </div>
        <span className={`editorial-image-tab__badge editorial-image-tab__badge--${image.imageStatus}`}>
          {getImageStatusLabel(image.imageStatus, image)}
        </span>
      </header>

      {canWriteFiles === false && hasGeneratedImage(image) && (
        <div className="editorial-image-tab__warning" role="alert">
          <p>{SHOPIFY_SCOPE_MISSING_WARNING}</p>
        </div>
      )}

      {storageWarning && hasGeneratedImage(image) && (
        <div className="editorial-image-tab__warning" role="alert">
          <p>{storageWarning}</p>
          {showRetryUpload && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              onClick={onRetryUpload}
              disabled={busy || canWriteFiles === false}
            >
              {retryUploadLoading ? "Upload in corso…" : "Riprova upload su Shopify"}
            </button>
          )}
        </div>
      )}

      {image.imageStatus === "uploaded" && hasShopifyCdnUrl(image) && (
        <div className="editorial-image-tab__success" role="status">
          <p>Immagine caricata su Shopify Files. Pronta per l&apos;approvazione.</p>
        </div>
      )}

      {imageIsStale && hasGeneratedImage(image) && (
        <div className="editorial-image-tab__warning" role="alert">
          <p>{IMAGE_STALE_MESSAGE}</p>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary gcr-btn--sm"
            onClick={onRegenerate}
            disabled={busy}
          >
            Rigenera immagine da articolo aggiornato
          </button>
        </div>
      )}

      {filenameStale && hasGeneratedImage(image) && (
        <div className="editorial-image-tab__warning" role="alert">
          <p>{FILENAME_STALE_MESSAGE}</p>
          {onSyncFromTitle && (
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary gcr-btn--sm"
              onClick={onSyncFromTitle}
              disabled={busy}
            >
              {syncLoading ? "Aggiornamento…" : "Aggiorna nome file e ALT dal titolo articolo"}
            </button>
          )}
        </div>
      )}

      <section className="editorial-image-tab__meta">
        <div>
          <span className="editorial-image-tab__meta-label">Formato finale</span>
          <strong>{formatImageFinalSize(image)}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">Formato generazione</span>
          <strong>{formatImageProviderSize(image)}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">Post-processing</span>
          <strong>{IMAGE_POST_PROCESSING_LABEL}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">Filename SEO</span>
          <strong>{image.imageFilename ?? "—"}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">ALT immagine</span>
          <strong>{altText}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">Storage</span>
          <strong>{image.imageStorageProvider ?? "shopify_files"}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">Modello</span>
          <strong>{image.imageModel ?? "—"}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">Costo stimato</span>
          <strong>{formatImageCost(image.imageGenerationCost)}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">Ultimo aggiornamento</span>
          <strong>{formatImageUpdatedAt(image.updatedAt)}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">Sync Shopify</span>
          <strong>{getImageSyncLabel(image)}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">Hash articolo sorgente</span>
          <strong className="editorial-image-tab__hash">
            {image.generatedFromArticleHash ?? image.sourceArticleHash ?? "—"}
          </strong>
        </div>
      </section>

      <section className="editorial-image-tab__preview">
        {previewUrl ? (
          <img
            src={previewUrl}
            alt={altText}
            className="editorial-image-tab__image"
            style={{ aspectRatio: "3 / 2", width: "100%", maxWidth: "720px", objectFit: "cover" }}
          />
        ) : (
          <div className="editorial-image-tab__placeholder">Nessuna anteprima disponibile</div>
        )}
      </section>

      <section className="editorial-image-tab__actions">
        {!hasGeneratedImage(image) ? (
          <button
            type="button"
            className="gcr-btn gcr-btn--primary"
            onClick={onGenerate}
            disabled={busy}
          >
            {generateLoading ? "Generazione…" : "Genera immagine"}
          </button>
        ) : (
          <>
            <button
              type="button"
              className="gcr-btn gcr-btn--secondary"
              onClick={onRegenerate}
              disabled={busy}
            >
              {generateLoading ? "Rigenerazione…" : "Rigenera"}
            </button>
            {(image.imageStatus === "generated" || image.imageStatus === "uploaded") && (
              <button
                type="button"
                className="gcr-btn gcr-btn--primary"
                onClick={onApprove}
                disabled={busy || !approveAllowed}
                title={
                  approveAllowed
                    ? undefined
                    : "Serve un URL CDN Shopify prima di approvare l'immagine."
                }
              >
                {approveLoading ? "Approvazione…" : "Approva immagine"}
              </button>
            )}
            {showRetryUpload && (
              <button
                type="button"
                className="gcr-btn gcr-btn--secondary"
                onClick={onRetryUpload}
                disabled={busy || canWriteFiles === false}
              >
                {retryUploadLoading ? "Upload in corso…" : "Riprova upload su Shopify"}
              </button>
            )}
            <button
              type="button"
              className="gcr-btn gcr-btn--danger"
              onClick={onRemove}
              disabled={busy}
            >
              {removeLoading ? "Rimozione…" : "Rimuovi immagine"}
            </button>
          </>
        )}
      </section>

      {hasGeneratedImage(image) && (
        <section className="editorial-image-tab__section">
          <label className="gcr-field">
            <span className="gcr-field__label">Istruzioni di modifica</span>
            <textarea
              className="gcr-input gcr-input--textarea"
              rows={4}
              value={revisionNote}
              onChange={(e) => onRevisionNoteChange(e.target.value)}
              placeholder="Es. più luce naturale, meno prodotti in primo piano, sfondo neutro…"
            />
          </label>
          <button
            type="button"
            className="gcr-btn gcr-btn--secondary"
            onClick={onApplyEdit}
            disabled={busy || !revisionNote.trim()}
          >
            {editLoading ? "Applicazione…" : "Applica modifica"}
          </button>
        </section>
      )}

      {hasGeneratedImage(image) && (
        <details className="editorial-image-tab__section editorial-ai-info__details">
          <summary>Dettagli avanzati</summary>
          <div className="editorial-ai-info__section">
            <h6 className="editorial-ai-info__section-title">Prompt usato</h6>
            {image.imagePrompt ? (
              <pre className="editorial-image-tab__prompt">{image.imagePrompt}</pre>
            ) : (
              <p className="editorial-ai-info__empty">—</p>
            )}
          </div>
          {image.imageRevisionNote && (
            <div className="editorial-ai-info__section">
              <h6 className="editorial-ai-info__section-title">Istruzioni modifica</h6>
              <p>{image.imageRevisionNote}</p>
            </div>
          )}
          {image.imageRevisedPrompt && (
            <div className="editorial-ai-info__section">
              <h6 className="editorial-ai-info__section-title">Prompt rivisto</h6>
              <pre className="editorial-image-tab__prompt">{image.imageRevisedPrompt}</pre>
            </div>
          )}
          <div className="editorial-ai-info__section">
            <h6 className="editorial-ai-info__section-title">Dettagli tecnici</h6>
            <ul className="editorial-ai-info__list editorial-ai-info__list--technical">
              <li>
                <strong>Provider requested:</strong> {image.imageProviderRequestedSize ?? image.imageProviderSize ?? "—"}
              </li>
              <li>
                <strong>Provider returned:</strong> {image.imageProviderReturnedSize ?? "—"}
              </li>
              <li>
                <strong>Post-processing:</strong> {image.imagePostProcessingApplied ?? IMAGE_POST_PROCESSING_LABEL}
              </li>
              <li>
                <strong>Storage:</strong> {image.imageStorageProvider ?? "shopify_files"}
              </li>
              <li>
                <strong>Shopify file status:</strong> {image.shopifyFileStatus ?? "—"}
              </li>
              <li>
                <strong>Shopify media GID:</strong> {image.shopifyMediaGid ?? "—"}
              </li>
              <li>
                <strong>Uploaded at:</strong> {formatImageUpdatedAt(image.shopifyUploadedAt)}
              </li>
              <li>
                <strong>Synced at:</strong> {formatImageUpdatedAt(image.shopifyImageSyncedAt)}
              </li>
              <li>
                <strong>Approved hash:</strong> {image.approvedImageHash ?? "—"}
              </li>
              <li>
                <strong>Skill pack:</strong> {image.skillPackUsed || "—"} {image.skillPackVersion ? `(${image.skillPackVersion})` : ""}
              </li>
            </ul>
          </div>
          {image.aiGeneration && (
            <div className="editorial-ai-info__section">
              <h6 className="editorial-ai-info__section-title">Generazione AI prompt</h6>
              <ul className="editorial-ai-info__list">
                <li>
                  <strong>Modello:</strong> {image.aiGeneration.model ?? "—"}
                </li>
                <li>
                  <strong>Costo:</strong> {formatImageCost(image.aiGeneration.estimatedTotalCost)}
                </li>
                <li>
                  <strong>Token:</strong> {image.aiGeneration.inputTokens ?? "—"} / {image.aiGeneration.outputTokens ?? "—"}
                </li>
              </ul>
            </div>
          )}
        </details>
      )}
    </div>
  );
}
