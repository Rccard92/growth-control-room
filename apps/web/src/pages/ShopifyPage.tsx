import { useParams } from "react-router-dom";
import { Card, PageHeader } from "@gcr/ui";

export function ShopifyPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <>
      <PageHeader
        title="Shopify"
        subtitle="Store, ordini, prodotti e inventario"
        breadcrumb={[
          { label: "Progetti", href: "/projects" },
          { label: id ?? "", href: `/projects/${id}` },
          { label: "Shopify" },
        ]}
      />
      <Card title="Connessione Shopify">
        <p style={{ fontSize: "0.875rem", color: "#6b7280", margin: "0 0 1rem" }}>
          L&apos;integrazione Shopify non è ancora implementata. Questa pagina
          conterrà la configurazione OAuth e la sincronizzazione dello store.
        </p>
        <ul style={{ fontSize: "0.875rem", color: "#374151", paddingLeft: "1.25rem", margin: 0 }}>
          <li>Autenticazione OAuth con Shopify Admin API</li>
          <li>Sincronizzazione prodotti e ordini</li>
          <li>Metriche vendite e inventario</li>
        </ul>
      </Card>
    </>
  );
}
