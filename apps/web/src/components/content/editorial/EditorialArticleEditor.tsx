import type { EditorialArticlePayload } from "@gcr/shared";
import { AutoResizeTextarea } from "../../ui/AutoResizeTextarea";
import { listToTextarea, textareaToList } from "./editorial-article-utils";

interface EditorialArticleEditorProps {
  value: EditorialArticlePayload;
  onChange: (value: EditorialArticlePayload) => void;
  bodyMode: "html" | "markdown";
  onBodyModeChange: (mode: "html" | "markdown") => void;
}

export function EditorialArticleEditor({
  value,
  onChange,
  bodyMode,
  onBodyModeChange,
}: EditorialArticleEditorProps) {
  function patch(partial: Partial<EditorialArticlePayload>) {
    onChange({ ...value, ...partial });
  }

  return (
    <div className="editorial-article-editor">
      <label className="gcr-field">
        <span className="gcr-field__label">Titolo articolo</span>
        <input
          className="gcr-input"
          value={value.title}
          onChange={(e) => patch({ title: e.target.value })}
        />
      </label>

      <label className="gcr-field">
        <span className="gcr-field__label">Handle (slug URL)</span>
        <input
          className="gcr-input"
          value={value.handle}
          onChange={(e) => patch({ handle: e.target.value })}
        />
      </label>

      <AutoResizeTextarea
        label="Excerpt"
        value={value.excerpt}
        onChange={(excerpt) => patch({ excerpt })}
        minRows={2}
        maxRows={6}
      />

      <div className="editorial-article-editor__body-toggle">
        <span className="gcr-field__label">Corpo articolo</span>
        <div className="editorial-article-subtabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={bodyMode === "html"}
            className={[
              "editorial-article-subtabs__tab",
              bodyMode === "html" ? "editorial-article-subtabs__tab--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onBodyModeChange("html")}
          >
            HTML
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={bodyMode === "markdown"}
            className={[
              "editorial-article-subtabs__tab",
              bodyMode === "markdown" ? "editorial-article-subtabs__tab--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onBodyModeChange("markdown")}
          >
            Markdown
          </button>
        </div>
      </div>

      {bodyMode === "html" ? (
        <AutoResizeTextarea
          value={value.bodyHtml}
          onChange={(bodyHtml) => patch({ bodyHtml })}
          minRows={8}
          maxRows={24}
          placeholder="<h2>...</h2><p>...</p>"
        />
      ) : (
        <AutoResizeTextarea
          value={value.bodyMarkdown}
          onChange={(bodyMarkdown) => patch({ bodyMarkdown })}
          minRows={8}
          maxRows={24}
          placeholder="## Titolo sezione"
        />
      )}

      <label className="gcr-field">
        <span className="gcr-field__label">SEO title</span>
        <input
          className="gcr-input"
          value={value.seoTitle}
          onChange={(e) => patch({ seoTitle: e.target.value })}
        />
      </label>

      <AutoResizeTextarea
        label="Meta description"
        value={value.metaDescription}
        onChange={(metaDescription) => patch({ metaDescription })}
        minRows={2}
        maxRows={6}
      />

      <AutoResizeTextarea
        label="Tags (uno per riga)"
        value={listToTextarea(value.tags)}
        onChange={(text) => patch({ tags: textareaToList(text) })}
        minRows={2}
        maxRows={8}
      />

      <AutoResizeTextarea
        label="CTA"
        value={value.cta}
        onChange={(cta) => patch({ cta })}
        minRows={2}
        maxRows={4}
      />

      {value.warnings.length > 0 && (
        <div className="editorial-article-editor__warnings gcr-card">
          <span className="gcr-field__label">Warning</span>
          <ul>
            {value.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
