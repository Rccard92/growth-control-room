import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Project } from "@gcr/shared";
import { Button, Card, PageHeader } from "@gcr/ui";
import { apiFetch } from "../lib/api";

export function NewProjectPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const project = await apiFetch<Project>("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || null,
        }),
      });
      navigate(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore durante la creazione");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Nuovo progetto"
        subtitle="Crea un nuovo progetto per monitorare un brand"
        breadcrumb={[
          { label: "Progetti", href: "/projects" },
          { label: "Nuovo" },
        ]}
      />
      <Card title="Dettagli progetto">
        <form
          style={{ display: "flex", flexDirection: "column", gap: "1rem", maxWidth: "24rem" }}
          onSubmit={handleSubmit}
        >
          <div className="login-page__field">
            <label htmlFor="name">Nome progetto</label>
            <input
              id="name"
              type="text"
              placeholder="Es. Brand XYZ"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </div>
          <div className="login-page__field">
            <label htmlFor="description">Descrizione</label>
            <input
              id="description"
              type="text"
              placeholder="Breve descrizione (opzionale)"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>
          {error && (
            <p style={{ color: "#dc2626", fontSize: "0.875rem", margin: 0 }}>{error}</p>
          )}
          <Button type="submit" disabled={submitting || !name.trim()}>
            {submitting ? "Creazione…" : "Crea progetto"}
          </Button>
        </form>
      </Card>
    </>
  );
}
