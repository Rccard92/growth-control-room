export type ProjectStatus = "active" | "archived";

export interface Project {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  publicSiteUrl?: string | null;
  searchConsoleSiteUrl?: string | null;
  googleAnalyticsPropertyId?: string | null;
  googleAnalyticsPropertyName?: string | null;
  status: ProjectStatus;
  createdAt: string;
  updatedAt: string;
}

export interface CreateProjectInput {
  name: string;
  description?: string | null;
  publicSiteUrl?: string | null;
}

export interface UpdateProjectInput {
  name?: string;
  description?: string | null;
  publicSiteUrl?: string | null;
  searchConsoleSiteUrl?: string | null;
  googleAnalyticsPropertyId?: string | null;
  googleAnalyticsPropertyName?: string | null;
}
