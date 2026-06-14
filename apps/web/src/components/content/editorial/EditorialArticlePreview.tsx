import type { EditorialArticlePayload } from "@gcr/shared";
import { sanitizeArticleHtml } from "../../../lib/sanitizeHtml";

interface EditorialArticlePreviewProps {
  value: EditorialArticlePayload;
}

export function EditorialArticlePreview({ value }: EditorialArticlePreviewProps) {
  const safeHtml = sanitizeArticleHtml(value.bodyHtml);

  return (
    <div className="editorial-article-preview">
      <article className="editorial-article-preview__article">
        <h1 className="editorial-article-preview__title">
          {value.title || "Titolo articolo"}
        </h1>
        {value.excerpt && (
          <p className="editorial-article-preview__excerpt">{value.excerpt}</p>
        )}
        {safeHtml ? (
          <div
            className="editorial-article-preview__body"
            dangerouslySetInnerHTML={{ __html: safeHtml }}
          />
        ) : value.bodyMarkdown ? (
          <pre className="editorial-article-preview__markdown-fallback">
            {value.bodyMarkdown}
          </pre>
        ) : (
          <p className="gcr-card__description">Nessun contenuto da visualizzare.</p>
        )}
        {value.cta && (
          <p className="editorial-article-preview__cta">
            <strong>CTA:</strong> {value.cta}
          </p>
        )}
        {value.linkedProducts.length > 0 && (
          <div className="editorial-article-preview__products">
            <span className="gcr-field__label">Prodotti linkati</span>
            <ul>
              {value.linkedProducts.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </div>
        )}
      </article>

      <aside className="editorial-article-preview__seo gcr-card">
        <h4 className="gcr-card__title">Metadata SEO</h4>
        <dl className="editorial-article-preview__meta-list">
          <div>
            <dt>Handle</dt>
            <dd>{value.handle || "—"}</dd>
          </div>
          <div>
            <dt>SEO title</dt>
            <dd>{value.seoTitle || "—"}</dd>
          </div>
          <div>
            <dt>Meta description</dt>
            <dd>{value.metaDescription || "—"}</dd>
          </div>
          {value.tags.length > 0 && (
            <div>
              <dt>Tags</dt>
              <dd>{value.tags.join(", ")}</dd>
            </div>
          )}
        </dl>
      </aside>
    </div>
  );
}
