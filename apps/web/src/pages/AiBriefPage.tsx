import { useParams } from "react-router-dom";
import { Card, PageHeader } from "@gcr/ui";

export function AiBriefPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <>
      <PageHeader
        title="AI Brief"
        subtitle="Brief di marketing generati con AI"
        breadcrumb={[
          { label: "Progetti", href: "/projects" },
          { label: id ?? "", href: `/projects/${id}` },
          { label: "AI Brief" },
        ]}
      />
      <Card title="Genera brief">
        <p style={{ fontSize: "0.875rem", color: "#6b7280", margin: "0 0 1rem" }}>
          Le skill AI in <code>packages/skills</code> alimenteranno questa
          sezione per generare brief basati sui dati del progetto.
        </p>
        <ul style={{ fontSize: "0.875rem", color: "#374151", paddingLeft: "1.25rem", margin: 0 }}>
          <li>Analisi performance campagne</li>
          <li>Suggerimenti ottimizzazione</li>
          <li>Brief creativi per nuove iniziative</li>
        </ul>
      </Card>
    </>
  );
}
