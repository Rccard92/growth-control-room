import type { SeoSkillTargetType } from "@gcr/shared";

export type SeoAuditPresetLevel = "base" | "advanced" | "deep";

export interface SeoAuditPreset {
  key: string;
  title: string;
  subtitle: string;
  description: string;
  intent: string;
  targetType: SeoSkillTargetType;
  recommendedFor: string[];
  includedSkills: string[];
  level: SeoAuditPresetLevel;
  estimatedTimeLabel: string;
  ctaLabel: string;
  badge: string;
  checksLabel: string[];
  microcopy?: string;
}

export const SEO_AUDIT_PRESETS: SeoAuditPreset[] = [
  {
    key: "page_360",
    title: "Audit pagina 360°",
    subtitle: "Analisi completa di una singola pagina",
    description:
      "Analizza una singola pagina da tutti i punti di vista: SEO on-page, contenuto, schema, immagini, AI Search e conversione.",
    intent: "page_audit",
    targetType: "url",
    recommendedFor: ["Landing", "Pagine servizio", "Pagine istituzionali"],
    includedSkills: ["seo_page", "seo_content", "seo_schema", "seo_images", "seo_geo", "seo_sxo"],
    level: "deep",
    estimatedTimeLabel: "5–8 min",
    ctaLabel: "Analizza pagina",
    badge: "Consigliato",
    checksLabel: [
      "Title e meta description",
      "Heading e struttura contenuto",
      "Schema.org e JSON-LD",
      "Immagini e alt text",
      "Visibilità AI Search",
      "Segnali di conversione",
    ],
    microcopy:
      "Scelta consigliata se vuoi analizzare una landing o una pagina strategica.",
  },
  {
    key: "product_page",
    title: "Audit prodotto ecommerce",
    subtitle: "Ottimizzazione pagina prodotto",
    description:
      "Analizza una pagina prodotto per SEO, conversione, trust, contenuti, dati strutturati e obiezioni d'acquisto.",
    intent: "product_audit",
    targetType: "url",
    recommendedFor: ["Shopify", "Ecommerce", "Landing di vendita"],
    includedSkills: [
      "seo_page",
      "seo_ecommerce",
      "seo_content",
      "seo_schema",
      "seo_images",
      "seo_sxo",
    ],
    level: "deep",
    estimatedTimeLabel: "5–8 min",
    ctaLabel: "Analizza prodotto",
    badge: "Ecommerce",
    checksLabel: [
      "SEO on-page prodotto",
      "Trust e obiezioni",
      "Contenuto persuasivo",
      "Product schema",
      "Immagini prodotto",
      "CTA e conversione",
    ],
    microcopy:
      "Scelta consigliata per pagine prodotto Shopify, ecommerce e landing di vendita.",
  },
  {
    key: "ai_search",
    title: "Audit AI Search / GEO",
    subtitle: "Visibilità nei motori conversazionali",
    description:
      "Valuta quanto una pagina è chiara, citabile e adatta a comparire nelle risposte generate da AI e motori conversazionali.",
    intent: "ai_search_audit",
    targetType: "url",
    recommendedFor: ["Blog", "Guide", "Pagine informative"],
    includedSkills: ["seo_geo", "seo_content", "seo_schema", "seo_page"],
    level: "advanced",
    estimatedTimeLabel: "3–5 min",
    ctaLabel: "Analizza visibilità AI",
    badge: "AI Search",
    checksLabel: [
      "Chiarezza e citabilità",
      "Struttura informativa",
      "Schema e entità",
      "Segnali on-page",
    ],
  },
  {
    key: "technical_page",
    title: "Audit tecnico pagina",
    subtitle: "Controlli tecnici on-page",
    description:
      "Controlla title, meta, canonical, heading, schema, immagini e segnali tecnici on-page.",
    intent: "technical_audit",
    targetType: "url",
    recommendedFor: ["Dev", "SEO tecnico", "QA"],
    includedSkills: ["seo_page", "seo_technical", "seo_schema", "seo_images"],
    level: "base",
    estimatedTimeLabel: "3–5 min",
    ctaLabel: "Analizza tecnica",
    badge: "Tecnico",
    checksLabel: [
      "Title e meta",
      "Canonical e heading",
      "Schema markup",
      "Immagini tecniche",
    ],
  },
  {
    key: "content_conversion",
    title: "Audit contenuto e conversione",
    subtitle: "Qualità contenuto e UX",
    description:
      "Analizza qualità contenuto, intenzione di ricerca, trust, chiarezza, CTA e ostacoli alla conversione.",
    intent: "content_audit",
    targetType: "url",
    recommendedFor: ["Marketing", "Content", "CRO"],
    includedSkills: ["seo_content", "seo_sxo", "seo_ecommerce", "seo_page"],
    level: "advanced",
    estimatedTimeLabel: "4–6 min",
    ctaLabel: "Analizza contenuto",
    badge: "Contenuto",
    checksLabel: [
      "Qualità e intento",
      "Trust e chiarezza",
      "CTA e frizione",
      "Segnali ecommerce",
    ],
  },
  {
    key: "site_base",
    title: "Audit sito base",
    subtitle: "Prima fotografia SEO del sito",
    description:
      "Analisi iniziale del dominio/homepage. Utile per avere una prima fotografia SEO del sito.",
    intent: "site_audit",
    targetType: "url",
    recommendedFor: ["Homepage", "Dominio", "Primo audit"],
    includedSkills: ["seo_audit", "seo_technical", "seo_content", "seo_schema", "seo_images"],
    level: "base",
    estimatedTimeLabel: "5–8 min",
    ctaLabel: "Analizza sito",
    badge: "Sito",
    checksLabel: [
      "Audit generale",
      "Segnali tecnici",
      "Contenuto homepage",
      "Schema e immagini",
    ],
    microcopy:
      "Analisi iniziale della homepage/dominio. Non sostituisce ancora un crawl completo multi-pagina. Crawl multi-pagina in arrivo con integrazione Firecrawl/DataForSEO.",
  },
  {
    key: "schema_only",
    title: "Audit dati strutturati",
    subtitle: "Schema.org e JSON-LD",
    description:
      "Controlla JSON-LD, Schema.org, Product, Breadcrumb, Organization e coerenza con il contenuto visibile.",
    intent: "schema_audit",
    targetType: "url",
    recommendedFor: ["Dev", "SEO tecnico"],
    includedSkills: ["seo_schema"],
    level: "base",
    estimatedTimeLabel: "2–3 min",
    ctaLabel: "Analizza schema",
    badge: "Schema",
    checksLabel: ["JSON-LD", "Product schema", "Breadcrumb", "Organization"],
  },
  {
    key: "custom",
    title: "Modalità avanzata",
    subtitle: "Selezione manuale skill",
    description: "Seleziona manualmente le skill da eseguire.",
    intent: "custom",
    targetType: "url",
    recommendedFor: ["Utenti esperti"],
    includedSkills: [],
    level: "advanced",
    estimatedTimeLabel: "Variabile",
    ctaLabel: "Configura manualmente",
    badge: "Avanzato",
    checksLabel: ["Skill personalizzate"],
    microcopy: "Usala solo se sai già quali controlli vuoi eseguire.",
  },
];

export function getAuditPreset(key: string): SeoAuditPreset | undefined {
  return SEO_AUDIT_PRESETS.find((preset) => preset.key === key);
}

export function getPrimaryAuditPresets(): SeoAuditPreset[] {
  return SEO_AUDIT_PRESETS;
}

export function formatAuditPresetLevel(level: SeoAuditPresetLevel): string {
  const labels: Record<SeoAuditPresetLevel, string> = {
    base: "Base",
    advanced: "Avanzato",
    deep: "Completo",
  };
  return labels[level];
}

export function formatAuditTargetType(targetType: SeoSkillTargetType): string {
  const labels: Record<string, string> = {
    url: "URL pagina",
    domain: "Dominio",
    shopify_product: "Prodotto Shopify",
    shopify_collection: "Collezione Shopify",
    article: "Articolo",
  };
  return labels[targetType] ?? targetType;
}
