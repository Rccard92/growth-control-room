export const PROJECT_NAV = [
  { to: "", label: "Control Room", icon: "◉", end: true as const },
  { to: "brand-intelligence", label: "Brand Intelligence", icon: "◎" },
  { to: "integrations", label: "Integration Center", icon: "⬡" },
  { to: "shopify", label: "Shopify", icon: "🛍" },
  { to: "content", label: "Content SEO", icon: "✎" },
  { to: "changelog", label: "Changelog", icon: "📋" },
  { to: "ai-brief", label: "AI Brief", icon: "✦" },
] as const;

export const APP_ROUTES = {
  login: "/login",
  privacy: "/privacy",
  projects: "/projects",
  newProject: "/projects/new",
  project: (id: string) => `/projects/${id}`,
  projectBrandIntelligence: (id: string) => `/projects/${id}/brand-intelligence`,
  projectBrandIntelligenceImport: (id: string) => `/projects/${id}/brand-intelligence/import`,
  projectIntegrations: (id: string) => `/projects/${id}/integrations`,
  projectShopify: (id: string) => `/projects/${id}/shopify`,
  projectShopifyConnect: (id: string) => `/projects/${id}/shopify/connect`,
  projectContent: (id: string) => `/projects/${id}/content`,
  projectChangelog: (id: string) => `/projects/${id}/changelog`,
  projectAiBrief: (id: string) => `/projects/${id}/ai-brief`,
} as const;
