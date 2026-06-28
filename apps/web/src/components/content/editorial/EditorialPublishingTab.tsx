import { useState } from "react";
import type {
  ContentSeoEditorialItem,
  ContentSeoEditorialStatus,
  EditorialPublishingPayload,
  EditorialPublishMode,
  ShopifyBlogListItem,
} from "@gcr/shared";
import { AppSelect } from "../../ui/AppSelect";
import { AutoResizeTextarea } from "../../ui/AutoResizeTextarea";
import { EditorialArticlePreview } from "./EditorialArticlePreview";
import {
  getPublishStatusLabel,
  getPublishingSeoWarnings,
  inputToTags,
  META_DESCRIPTION_MAX,
  SEO_TITLE_MAX,
  tagsToInput,
} from "./editorial-publishing-utils";

interface EditorialPublishingTabProps {
  item: ContentSeoEditorialItem;
  status: ContentSeoEditorialStatus;
  hasArticle: boolean;
  publishingStale: boolean;
  staleDismissed: boolean;
  publishBlockedByStale?: boolean;
  publishBlockedBySeo?: boolean;
  publishError?: string | null;
  publishing: EditorialPublishingPayload;
  onChange: (value: EditorialPublishingPayload) => void;
  onSyncFromArticle: () => void;
  onDismissStale: () => void;
  onDisconnectShopify: () => void;
  syncLoading?: boolean;
  disconnectLoading?: boolean;
  blogs: ShopifyBlogListItem[];
  blogsLoading: boolean;
  blogsSyncRequired: boolean;
  canWriteContent: boolean;
  scopesLoading: boolean;
}

export function EditorialPublishingTab({
  item,
  status,
  hasArticle,
  publishingStale,
  staleDismissed,
  publishBlockedByStale = false,
  publishBlockedBySeo = false,
  publishError = null,
  publishing,
  onChange,
  onSyncFromArticle,
  onDismissStale,
  onDisconnectShopify,
  syncLoading = false,
  disconnectLoading = false,
  blogs,
  blogsLoading,
  blogsSyncRequired,
  canWriteContent,
  scopesLoading,
}: EditorialPublishingTabProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const readyToPublish = status === "ready_to_publish";
  const selectedBlog = blogs.find((b) => b.id === publishing.blogId);
  const authorMissing = !publishing.author.trim();
  const publishBlocked = !canWriteContent || scopesLoading || authorMissing;
  const publishActionsDisabled = !readyToPublish || publishBlocked;
  const hasShopifyLink = Boolean(item.shopifyArticleGid);
  const shopifyActionVerb = hasShopifyLink ? "aggiornato" : "creato";
  const seoTitleMissing = !publishing.seoTitle.trim();
  const metaDescriptionMissing = !publishing.metaDescription.trim();
  const seoWarnings = getPublishingSeoWarnings(publishing);

  function patch(partial: Partial<EditorialPublishingPayload>) {
    onChange({ ...publishing, ...partial });
  }

  function handleBlogChange(blogId: string) {
    const blog = blogs.find((b) => b.id === blogId);
    patch({
      blogId: blogId || null,
      blogGid: blog?.gid ?? null,
    });
  }

  function handleModeChange(mode: EditorialPublishMode) {
    if (mode === "schedule") return;
    patch({ mode });
  }

  if (!hasArticle) {
    return (
      <div className="editorial-publishing-tab editorial-publishing-tab--empty">
        <p>Genera prima l&apos;articolo per configurare la pubblicazione su Shopify.</p>
      </div>
    );
  }

  return (
    <div className="editorial-publishing-tab">
      {!readyToPublish && (
        <div className="gcr-alert gcr-alert--warning">
          L&apos;articolo non è ancora marcato come pronto per la pubblicazione. Puoi
          preparare il form, ma le azioni Shopify restano disabilitate finché non lo
          segni pronto.
        </div>
      )}

      {publishBlocked && !scopesLoading && (
        <div className="gcr-alert gcr-alert--warning">
          Serve il permesso Shopify <strong>write_content</strong>. Riconnetti Shopify con
          gli scope aggiornati per creare articoli nel blog.
        </div>
      )}

      {authorMissing && (
        <div className="gcr-alert gcr-alert--warning">
          Autore obbligatorio per creare l&apos;articolo su Shopify.
        </div>
      )}

      {publishError ? (
        <div className="gcr-alert gcr-alert--error">{publishError}</div>
      ) : (
        item.lastPublishError && (
          <div className="gcr-alert gcr-alert--error">{item.lastPublishError}</div>
        )
      )}

      {publishing.shopifySeoSynced === true && (
        <div className="gcr-alert gcr-alert--success">SEO Shopify sincronizzata</div>
      )}

      {publishing.shopifySeoSynced === false && publishing.shopifySeoError && (
        <div className="gcr-alert gcr-alert--warning">
          Articolo creato, ma SEO non sincronizzata: {publishing.shopifySeoError}
        </div>
      )}

      {publishingStale && !staleDismissed && (
        <div className="gcr-alert gcr-alert--warning editorial-publishing-tab__stale-banner">
          <p>
            L&apos;articolo è stato modificato dopo la preparazione dei dati di pubblicazione. I
            dati Shopify potrebbero essere vecchi.
          </p>
          <div className="editorial-publishing-tab__stale-actions">
            <button
              type="button"
              className="gcr-btn gcr-btn--primary gcr-btn--sm"
              disabled={syncLoading}
              onClick={onSyncFromArticle}
            >
              {syncLoading ? "Aggiornamento…" : "Aggiorna dati pubblicazione dall'articolo"}
            </button>
            <button
              type="button"
              className="gcr-btn gcr-btn--ghost gcr-btn--sm"
              onClick={onDismissStale}
            >
              Mantieni dati pubblicazione attuali
            </button>
          </div>
        </div>
      )}

      <div className="editorial-publishing-tab__summary">
        <p>
          Questo articolo verrà {shopifyActionVerb} nel blog Shopify:{" "}
          <strong>{selectedBlog?.title ?? "— seleziona un blog —"}</strong>
        </p>
        <p>
          Stato: <span className="editorial-publishing-tab__status">{getPublishStatusLabel(item.publishStatus)}</span>
        </p>
        {hasShopifyLink && item.publishStatus === "draft_created" && (
          <p className="editorial-publishing-tab__shopify-linked">Bozza Shopify già creata</p>
        )}
        {hasShopifyLink && item.publishStatus === "published" && (
          <p className="editorial-publishing-tab__shopify-linked">Articolo Shopify già collegato</p>
        )}
        {item.shopifyArticleAdminUrl && (
          <p>
            <a
              href={item.shopifyArticleAdminUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="gcr-link"
            >
              Apri in Shopify Admin
            </a>
          </p>
        )}
        {item.publishStatus === "published" && (
          <p className="editorial-publishing-tab__success">Articolo pubblicato su Shopify.</p>
        )}
      </div>

      {blogsSyncRequired && !blogsLoading && blogs.length === 0 && (
        <div className="gcr-alert gcr-alert--warning">
          Nessun blog Shopify sincronizzato. Connetti Shopify e verifica i permessi{" "}
          <strong>read_content</strong>.
        </div>
      )}

      <section className="editorial-publishing-tab__section">
        <h4>Contenuto</h4>
        <label className="gcr-field">
          <span className="gcr-field__label">Titolo</span>
          <input
            className="gcr-input"
            value={publishing.title}
            onChange={(e) => patch({ title: e.target.value })}
          />
        </label>
        <label className="gcr-field">
          <span className="gcr-field__label">Handle</span>
          <input
            className="gcr-input"
            value={publishing.handle}
            onChange={(e) => patch({ handle: e.target.value })}
          />
        </label>
        <div className="editorial-publishing-tab__body-header">
          <span className="gcr-field__label">Contenuto HTML</span>
          <button
            type="button"
            className="gcr-btn gcr-btn--ghost gcr-btn--sm"
            onClick={() => setShowPreview((v) => !v)}
          >
            {showPreview ? "Modifica HTML" : "Anteprima"}
          </button>
        </div>
        {showPreview ? (
          <EditorialArticlePreview
            value={{
              title: publishing.title,
              handle: publishing.handle,
              excerpt: publishing.excerpt,
              bodyHtml: publishing.bodyHtml,
              bodyMarkdown: "",
              seoTitle: publishing.seoTitle,
              metaDescription: publishing.metaDescription,
              tags: publishing.tags,
              linkedProducts: [],
              cta: "",
              status: "draft",
              warnings: [],
              brandContextUsed: [],
              generatedAt: "",
            }}
          />
        ) : (
          <AutoResizeTextarea
            label=""
            value={publishing.bodyHtml}
            onChange={(bodyHtml) => patch({ bodyHtml })}
            minRows={8}
            maxRows={24}
          />
        )}
        <AutoResizeTextarea
          label="Estratto"
          value={publishing.excerpt}
          onChange={(excerpt) => patch({ excerpt })}
          minRows={2}
          maxRows={6}
        />
      </section>

      <section className="editorial-publishing-tab__section">
        <h4>SEO</h4>
        <p className="editorial-publishing-tab__field-hint">
          Questi campi vengono inviati a Shopify come metafields SEO dell&apos;articolo.
        </p>
        <label
          className={[
            "gcr-field",
            seoTitleMissing ? "editorial-publishing-tab__field--required" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <span className="gcr-field__label">
            SEO title *{" "}
            <span className="editorial-publishing-tab__char-count">
              {publishing.seoTitle.length}/{SEO_TITLE_MAX}
            </span>
          </span>
          <input
            className="gcr-input"
            value={publishing.seoTitle}
            onChange={(e) => patch({ seoTitle: e.target.value })}
          />
        </label>
        {publishing.seoTitle.length > SEO_TITLE_MAX && (
          <p className="editorial-publishing-tab__field-warning">
            SEO title oltre la lunghezza consigliata ({SEO_TITLE_MAX} caratteri).
          </p>
        )}
        <div
          className={[
            "gcr-field",
            metaDescriptionMissing ? "editorial-publishing-tab__field--required" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <span className="gcr-field__label">
            Meta description *{" "}
            <span className="editorial-publishing-tab__char-count">
              {publishing.metaDescription.length}/{META_DESCRIPTION_MAX}
            </span>
          </span>
          <AutoResizeTextarea
            label=""
            value={publishing.metaDescription}
            onChange={(metaDescription) => patch({ metaDescription })}
            minRows={2}
            maxRows={5}
          />
        </div>
        {publishing.metaDescription.length > META_DESCRIPTION_MAX && (
          <p className="editorial-publishing-tab__field-warning">
            Meta description oltre la lunghezza consigliata ({META_DESCRIPTION_MAX} caratteri).
          </p>
        )}
        {seoWarnings.length > 0 && (
          <div className="gcr-alert gcr-alert--warning editorial-publishing-tab__seo-warnings">
            {seoWarnings.map((warning) => (
              <p key={warning}>{warning}</p>
            ))}
          </div>
        )}
        {publishBlockedBySeo && (
          <p className="editorial-publishing-tab__field-hint editorial-publishing-tab__field-hint--error">
            Compila SEO title e meta description per abilitare la pubblicazione su Shopify.
          </p>
        )}
      </section>

      <section className="editorial-publishing-tab__section">
        <h4>Organizzazione</h4>
        <label
          className={[
            "gcr-field",
            authorMissing ? "editorial-publishing-tab__field--required" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <span className="gcr-field__label">Autore *</span>
          <input
            className="gcr-input"
            value={publishing.author}
            onChange={(e) => patch({ author: e.target.value })}
            required
          />
        </label>
        <p className="editorial-publishing-tab__field-hint">
          Shopify richiede sempre un autore per i post blog.
        </p>
        <AppSelect
          label="Blog Shopify"
          value={publishing.blogId ?? ""}
          options={[
            { value: "", label: blogsLoading ? "Caricamento blog…" : "— Seleziona blog —" },
            ...blogs.map((blog) => ({ value: blog.id, label: blog.title })),
          ]}
          onChange={handleBlogChange}
        />
        <label className="gcr-field">
          <span className="gcr-field__label">Tags (separati da virgola)</span>
          <input
            className="gcr-input"
            value={tagsToInput(publishing.tags)}
            onChange={(e) => patch({ tags: inputToTags(e.target.value) })}
          />
        </label>
      </section>

      <section className="editorial-publishing-tab__section">
        <h4>Immagine (opzionale)</h4>
        <label className="gcr-field">
          <span className="gcr-field__label">URL immagine</span>
          <input
            className="gcr-input"
            value={publishing.imageUrl ?? ""}
            onChange={(e) => patch({ imageUrl: e.target.value || null })}
          />
        </label>
        <label className="gcr-field">
          <span className="gcr-field__label">Alt text</span>
          <input
            className="gcr-input"
            value={publishing.imageAlt ?? ""}
            onChange={(e) => patch({ imageAlt: e.target.value || null })}
          />
        </label>
      </section>

      <section className="editorial-publishing-tab__section">
        <h4>Visibilità</h4>
        <div className="editorial-publishing-tab__modes">
          <label className="editorial-publishing-tab__mode">
            <input
              type="radio"
              name={`publish-mode-${item.id}`}
              checked={publishing.mode === "draft"}
              onChange={() => handleModeChange("draft")}
            />
            Crea bozza Shopify (default)
          </label>
          <label className="editorial-publishing-tab__mode">
            <input
              type="radio"
              name={`publish-mode-${item.id}`}
              checked={publishing.mode === "publish_now"}
              onChange={() => handleModeChange("publish_now")}
              disabled={publishActionsDisabled || publishBlockedByStale || publishBlockedBySeo}
            />
            Pubblica subito
          </label>
          <label className="editorial-publishing-tab__mode editorial-publishing-tab__mode--disabled">
            <input type="radio" name={`publish-mode-${item.id}`} disabled />
            Programma pubblicazione — Disponibile nel prossimo step
          </label>
        </div>
      </section>

      <section className="editorial-publishing-tab__section">
        <button
          type="button"
          className="editorial-publishing-tab__advanced-toggle"
          onClick={() => setAdvancedOpen((v) => !v)}
        >
          {advancedOpen ? "Nascondi avanzate" : "Mostra avanzate"}
        </button>
        {advancedOpen && (
          <>
            <label className="gcr-field">
              <span className="gcr-field__label">Template suffix</span>
              <input
                className="gcr-input"
                value={publishing.templateSuffix ?? ""}
                onChange={(e) => patch({ templateSuffix: e.target.value || null })}
              />
            </label>
            {hasShopifyLink && (
              <div className="editorial-publishing-tab__disconnect">
                <button
                  type="button"
                  className="gcr-btn gcr-btn--danger gcr-btn--sm"
                  disabled={disconnectLoading}
                  onClick={onDisconnectShopify}
                >
                  {disconnectLoading ? "Scollegamento…" : "Scollega articolo Shopify"}
                </button>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
