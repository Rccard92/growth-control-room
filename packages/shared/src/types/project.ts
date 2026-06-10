export interface Project {
  id: string;
  name: string;
  brand: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateProjectInput {
  name: string;
  brand: string;
}
