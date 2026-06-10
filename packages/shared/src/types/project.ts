export type ProjectStatus = "active" | "archived";

export interface Project {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  status: ProjectStatus;
  createdAt: string;
  updatedAt: string;
}

export interface CreateProjectInput {
  name: string;
  description?: string | null;
}
