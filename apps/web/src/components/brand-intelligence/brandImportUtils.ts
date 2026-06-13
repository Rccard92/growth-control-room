const SECTION_LABELS: Record<string, string> = {
  brand_profile: "Brand Profile",
  voice_tone: "Voice & Tone",
  products_categories: "Products & Categories",
  product_knowledge: "Products",
  category_knowledge: "Categories",
  audience: "Audience",
  claims_compliance: "Claims & Compliance",
  seo_strategy: "SEO Strategy",
  content_pillars: "Content Pillars",
  ai_guardrails: "AI Guardrails",
  assets: "Assets",
  unknown: "Da classificare",
};

export function targetSectionLabel(section: string): string {
  return SECTION_LABELS[section] ?? section;
}

export const TARGET_SECTIONS = Object.keys(SECTION_LABELS).filter((k) => k !== "unknown");
