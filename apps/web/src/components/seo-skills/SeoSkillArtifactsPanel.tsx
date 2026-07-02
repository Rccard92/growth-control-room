import { useState } from "react";
import type { SeoSkillArtifactsView } from "./seo-skills-utils";
import { copyTextToClipboard } from "./seo-skills-utils";

interface SeoSkillArtifactsPanelProps {
  artifacts: SeoSkillArtifactsView;
}

function CopyButton({
  label,
  text,
}: {
  label: string;
  text: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const ok = await copyTextToClipboard(text);
    if (ok) {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    }
  };

  return (
    <button type="button" className="gcr-btn gcr-btn--secondary gcr-btn--sm" onClick={() => void handleCopy()}>
      {copied ? "Copiato" : label}
    </button>
  );
}

export function SeoSkillArtifactsPanel({ artifacts }: SeoSkillArtifactsPanelProps) {
  const hasJsonLd = artifacts.jsonLd.length > 0;
  const hasMarkdown = Boolean(artifacts.markdownReport.trim());
  const hasPrompts = artifacts.shopifySidekickPrompts.length > 0;
  const hasNotes = artifacts.implementationNotes.length > 0;

  if (!hasJsonLd && !hasMarkdown && !hasPrompts && !hasNotes) {
    return <p className="seo-skill-result-section__empty">Nessun artifact generato.</p>;
  }

  const jsonLdText = hasJsonLd
    ? JSON.stringify(artifacts.jsonLd, null, 2)
    : "";

  return (
    <div className="seo-skill-artifacts">
      {hasMarkdown && (
        <section className="seo-skill-artifacts__section">
          <h5 className="seo-skill-artifacts__title">Report markdown</h5>
          <div className="seo-skill-artifacts__markdown">{artifacts.markdownReport}</div>
        </section>
      )}

      {hasJsonLd && (
        <section className="seo-skill-artifacts__section">
          <div className="seo-skill-artifacts__header">
            <h5 className="seo-skill-artifacts__title">JSON-LD suggerito</h5>
            <CopyButton label="Copia JSON-LD" text={jsonLdText} />
          </div>
          <details className="seo-skill-artifacts__details">
            <summary>Mostra JSON-LD</summary>
            <pre className="seo-skill-debug-json">{jsonLdText}</pre>
          </details>
        </section>
      )}

      {hasPrompts && (
        <section className="seo-skill-artifacts__section">
          <h5 className="seo-skill-artifacts__title">Shopify Sidekick prompts</h5>
          <ul className="seo-skill-artifacts__prompt-list">
            {artifacts.shopifySidekickPrompts.map((prompt, index) => (
              <li key={`prompt-${index}`} className="seo-skill-artifacts__prompt-item">
                <p>{prompt}</p>
                <CopyButton label="Copia prompt" text={prompt} />
              </li>
            ))}
          </ul>
        </section>
      )}

      {hasNotes && (
        <section className="seo-skill-artifacts__section">
          <h5 className="seo-skill-artifacts__title">Note implementative</h5>
          <ul className="seo-skill-artifacts__notes-list">
            {artifacts.implementationNotes.map((note, index) => (
              <li key={`note-${index}`}>{note}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
