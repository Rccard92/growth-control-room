import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "../components/PageHeader";
import { isApiBaseConfigured } from "../lib/api";
import { useCreateProject } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";

export function NewProjectPage() {
  const navigate = useNavigate();
  const createProject = useCreateProject();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const apiConfigured = isApiBaseConfigured();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const project = await createProject.mutateAsync({
      name: name.trim(),
      description: description.trim() || null,
    });
    navigate(APP_ROUTES.project(project.id));
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="Nuovo progetto"
        subtitle="Configura una nuova control room per un brand"
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: "Nuovo" },
        ]}
      />
      {!apiConfigured && (
        <div className="gcr-alert gcr-alert--error" style={{ marginBottom: "1rem" }}>
          VITE_API_URL non configurato: imposta l&apos;URL pubblico dell&apos;API su Railway
          (senza <code>/api</code> finale) e rebuild del servizio WEB.
        </div>
      )}
      <div className="gcr-card" style={{ maxWidth: 480 }}>
        <form
          style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}
          onSubmit={handleSubmit}
        >
          <div className="gcr-field">
            <label htmlFor="name">Nome progetto</label>
            <input
              id="name"
              type="text"
              placeholder="Es. Brand XYZ"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="gcr-field">
            <label htmlFor="description">Descrizione</label>
            <input
              id="description"
              type="text"
              placeholder="Breve descrizione (opzionale)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          {createProject.isError && (
            <div className="gcr-alert gcr-alert--error">
              {createProject.error.message}
            </div>
          )}
          <button
            type="submit"
            className="gcr-btn gcr-btn--primary"
            disabled={createProject.isPending || !name.trim() || !apiConfigured}
          >
            {createProject.isPending ? "Creazione…" : "Crea progetto"}
          </button>
        </form>
      </div>
    </motion.div>
  );
}
