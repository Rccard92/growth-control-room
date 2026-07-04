export const PROJECT_NAV = [
  { to: "", label: "Control Room", icon: "◉", end: true as const },
  { to: "audit", label: "Growth Audit", icon: "↗" },
  { to: "brand-intelligence", label: "Brand Intelligence", icon: "◎" },
  { to: "integrations", label: "Integration Center", icon: "⬡" },
  { to: "shopify", label: "Shopify", icon: "🛍" },
  { to: "content", label: "Content SEO", icon: "✎" },
  { to: "changelog", label: "Changelog", icon: "📋" },
  { to: "ai-brief", label: "AI Brief", icon: "✦" },
  { to: "ai-costs", label: "AI Costs", icon: "◈" },
] as const;

export const APP_ROUTES = {
  login: "/login",
  privacy: "/privacy",
  projects: "/projects",
  newProject: "/projects/new",
  project: (id: string) => `/projects/${id}`,
  projectGrowthAudit: (id: string) => `/projects/${id}/audit`,
  projectBrandIntelligence: (id: string) => `/projects/${id}/brand-intelligence`,
  projectIntegrations: (id: string) => `/projects/${id}/integrations`,
  projectShopify: (id: string) => `/projects/${id}/shopify`,
  projectShopifyConnect: (id: string) => `/projects/${id}/shopify/connect`,
  projectContent: (id: string) => `/projects/${id}/content`,
  projectChangelog: (id: string) => `/projects/${id}/changelog`,
  projectAiBrief: (id: string) => `/projects/${id}/ai-brief`,
  projectAiCosts: (id: string) => `/projects/${id}/ai-costs`,
} as const;
