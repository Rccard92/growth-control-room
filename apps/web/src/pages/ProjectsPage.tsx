import { Link } from "react-router-dom";
import { Button, Card, PageHeader } from "@gcr/ui";

export function ProjectsPage() {
  return (
    <>
      <PageHeader
        title="Progetti"
        subtitle="Gestisci i tuoi brand e-commerce e marketing"
        actions={
          <Link to="/projects/new">
            <Button>Nuovo progetto</Button>
          </Link>
        }
      />
      <div className="placeholder-grid">
        <Card title="Demo Brand" description="Brand di esempio — placeholder">
          <Link to="/projects/demo">
            <Button variant="secondary">Apri progetto</Button>
          </Link>
        </Card>
      </div>
    </>
  );
}
