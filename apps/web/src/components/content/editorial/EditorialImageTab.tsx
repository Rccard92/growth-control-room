import { useState } from "react";
import type { EditorialArticlePayload, EditorialImagePayload } from "@gcr/shared";
import { buildEditorialImagePreviewUrl } from "../../../lib/content-api";
import {
  FILENAME_STALE_MESSAGE,
  formatImageCost,
  formatImageDimensions,
  formatImageUpdatedAt,
  getImageStatusLabel,
  hasGeneratedImage,
  IMAGE_STALE_MESSAGE,
  isImageFilenameStale,
  PUBLIC_STORAGE_WARNING,
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
  generateLoading?: boolean;
  editLoading?: boolean;
  approveLoading?: boolean;
  removeLoading?: boolean;
  syncLoading?: boolean;
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
  generateLoading = false,
  editLoading = false,
  approveLoading = false,
  removeLoading = false,
  syncLoading = false,
}: EditorialImageTabProps) {
  const [promptOpen, setPromptOpen] = useState(false);
  const previewUrl = buildEditorialImagePreviewUrl(projectId, itemId, image);
  const busy = generateLoading || editLoading || approveLoading || removeLoading || syncLoading;
  const altText = image.imageAlt ?? article?.title ?? "—";
  const filenameStale = article ? isImageFilenameStale(image, article.title) : false;

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
            Formato fisso 1600×900 JPG. Filename SEO e ALT sincronizzati al titolo articolo.
          </p>
        </div>
        <span className={`editorial-image-tab__badge editorial-image-tab__badge--${image.imageStatus}`}>
          {getImageStatusLabel(image.imageStatus)}
        </span>
      </header>

      {hasGeneratedImage(image) && !image.shopifyImageReady && (
        <div className="editorial-image-tab__warning" role="alert">
          <p>{PUBLIC_STORAGE_WARNING}</p>
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
          <span className="editorial-image-tab__meta-label">Filename SEO</span>
          <strong>{image.imageFilename ?? "—"}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">Dimensione</span>
          <strong>{formatImageDimensions(image)}</strong>
        </div>
        <div>
          <span className="editorial-image-tab__meta-label">ALT immagine</span>
          <strong>{altText}</strong>
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
          <span className="editorial-image-tab__meta-label">Hash articolo sorgente</span>
          <strong className="editorial-image-tab__hash">{image.sourceArticleHash ?? "—"}</strong>
        </div>
      </section>

      <section className="editorial-image-tab__preview">
        {previewUrl ? (
          <img src={previewUrl} alt={altText} className="editorial-image-tab__image" />
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
            {image.imageStatus === "generated" && (
              <button
                type="button"
                className="gcr-btn gcr-btn--primary"
                onClick={onApprove}
                disabled={busy}
              >
                {approveLoading ? "Approvazione…" : "Approva immagine"}
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

      {image.imagePrompt && (
        <section className="editorial-image-tab__section">
          <button
            type="button"
            className="editorial-image-tab__prompt-toggle"
            onClick={() => setPromptOpen((open) => !open)}
          >
            {promptOpen ? "Nascondi prompt usato" : "Mostra prompt usato"}
          </button>
          {promptOpen && (
            <pre className="editorial-image-tab__prompt">{image.imagePrompt}</pre>
          )}
        </section>
      )}
    </div>
  );
}
