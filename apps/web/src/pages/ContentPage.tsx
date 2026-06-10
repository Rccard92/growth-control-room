import { useParams } from "react-router-dom";
import { Card, PageHeader } from "@gcr/ui";

export function ContentPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <>
      <PageHeader
        title="Contenuti"
        subtitle="Gestione contenuti marketing e catalogo"
        breadcrumb={[
          { label: "Progetti", href: "/projects" },
          { label: id ?? "", href: `/projects/${id}` },
          { label: "Contenuti" },
        ]}
      />
      <Card title="Contenuti del progetto">
        <p style={{ fontSize: "0.875rem", color: "#6b7280", margin: 0 }}>
          Sezione placeholder per la gestione di contenuti, asset creativi e
          materiali di marketing collegati al brand.
        </p>
      </Card>
    </>
  );
}
