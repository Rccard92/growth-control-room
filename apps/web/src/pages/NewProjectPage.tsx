import { Button, Card, PageHeader } from "@gcr/ui";

export function NewProjectPage() {
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
          onSubmit={(e) => e.preventDefault()}
        >
          <div className="login-page__field">
            <label htmlFor="name">Nome progetto</label>
            <input id="name" type="text" placeholder="Es. Brand XYZ" />
          </div>
          <div className="login-page__field">
            <label htmlFor="brand">Brand</label>
            <input id="brand" type="text" placeholder="Es. XYZ Srl" />
          </div>
          <Button type="submit">Crea progetto</Button>
        </form>
        <p style={{ marginTop: "1rem", fontSize: "0.75rem", color: "#9ca3af" }}>
          Persistenza non ancora implementata — form placeholder.
        </p>
      </Card>
    </>
  );
}
