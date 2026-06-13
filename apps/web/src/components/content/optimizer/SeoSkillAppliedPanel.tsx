import type { SeoSkillMeta } from "@gcr/shared";

const DEFAULT_SKILL_META: SeoSkillMeta = {
  name: "GCR Shopify SEO Skill",
  version: "1.0.0",
  attribution: "Inspired by claude-seo ecommerce/images/content-brief rules (MIT)",
  scoreRuleCategories: [
    "Regole prodotto",
    "Regole metadata",
    "Regole immagini",
    "Regole contenuto",
    "Regole Shopify/GCR",
  ],
};

interface SeoSkillAppliedPanelProps {
  skillMeta?: SeoSkillMeta | null;
}

export function SeoSkillAppliedPanel({ skillMeta }: SeoSkillAppliedPanelProps) {
  const meta = skillMeta ?? DEFAULT_SKILL_META;

  return (
    <section className="seo-skill-applied">
      <h4>Skill SEO applicata</h4>
      <p className="seo-skill-applied__name">
        {meta.name} <span className="seo-skill-applied__version">v{meta.version}</span>
      </p>
      <p className="seo-skill-applied__attribution">{meta.attribution}</p>
      <p className="seo-skill-applied__info">
        Pack interno GCR — regole adattate da claude-seo (MIT). Reference in{" "}
        <code>packages/skills/seo/gcr-shopify-seo/</code>
      </p>
    </section>
  );
}
