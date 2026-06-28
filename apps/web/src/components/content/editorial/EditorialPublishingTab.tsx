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
  inputToTags,
  tagsToInput,
} from "./editorial-publishing-utils";

interface EditorialPublishingTabProps {
  item: ContentSeoEditorialItem;
  status: ContentSeoEditorialStatus;
  hasArticle: boolean;
  publishing: EditorialPublishingPayload;
  onChange: (value: EditorialPublishingPayload) => void;
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
  publishing,
  onChange,
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
  const publishBlocked = !canWriteContent || scopesLoading;
  const publishActionsDisabled = !readyToPublish || publishBlocked;

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

      {item.lastPublishError && (
        <div className="gcr-alert gcr-alert--error">{item.lastPublishError}</div>
      )}

      <div className="editorial-publishing-tab__summary">
        <p>
          Questo articolo verrà creato nel blog Shopify:{" "}
          <strong>{selectedBlog?.title ?? "— seleziona un blog —"}</strong>
        </p>
        <p>
          Stato: <span className="editorial-publishing-tab__status">{getPublishStatusLabel(item.publishStatus)}</span>
        </p>
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
        <label className="gcr-field">
          <span className="gcr-field__label">SEO title</span>
          <input
            className="gcr-input"
            value={publishing.seoTitle}
            onChange={(e) => patch({ seoTitle: e.target.value })}
          />
        </label>
        <AutoResizeTextarea
          label="Meta description"
          value={publishing.metaDescription}
          onChange={(metaDescription) => patch({ metaDescription })}
          minRows={2}
          maxRows={5}
        />
      </section>

      <section className="editorial-publishing-tab__section">
        <h4>Organizzazione</h4>
        <label className="gcr-field">
          <span className="gcr-field__label">Autore</span>
          <input
            className="gcr-input"
            value={publishing.author}
            onChange={(e) => patch({ author: e.target.value })}
          />
        </label>
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
              disabled={publishActionsDisabled}
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
          <label className="gcr-field">
            <span className="gcr-field__label">Template suffix</span>
            <input
              className="gcr-input"
              value={publishing.templateSuffix ?? ""}
              onChange={(e) => patch({ templateSuffix: e.target.value || null })}
            />
          </label>
        )}
      </section>
    </div>
  );
}
