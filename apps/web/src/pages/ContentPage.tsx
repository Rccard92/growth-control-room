import { useState } from "react";
import { motion } from "framer-motion";
import { Link, useParams } from "react-router-dom";
import type { ContentSeoMainTab } from "@gcr/shared";
import { PageHeader } from "../components/PageHeader";
import {
  ContentSeoActionBar,
  type ContentSeoFeedback,
} from "../components/content/optimizer/ContentSeoActionBar";
import { SeoOptimizerRoom } from "../components/content/optimizer/SeoOptimizerRoom";
import { ContentSeoEditorialRoom } from "../components/content/editorial/ContentSeoEditorialRoom";
import { useProject } from "../hooks/useProjects";
import { useShopifyStatus } from "../hooks/useShopify";
import { APP_ROUTES } from "../routes/config";

const MAIN_TABS: { id: ContentSeoMainTab; label: string }[] = [
  { id: "products", label: "Prodotti & Categorie" },
  { id: "editorial", label: "Blog & Ricette" },
];

export function ContentPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  const { data: project } = useProject(id);
  const { data: shopifyStatus } = useShopifyStatus(id);
  const connected = shopifyStatus?.connected ?? false;
  const [tab, setTab] = useState<ContentSeoMainTab>("products");
  const [feedback, setFeedback] = useState<ContentSeoFeedback | null>(null);

  return (
    <motion.div
      className="content-seo-page"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <PageHeader
        title="Content SEO"
        subtitle="Ottimizza prodotti e categorie Shopify, pianifica blog e ricette nel calendario editoriale."
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Content SEO" },
        ]}
        actions={
          tab === "products" && connected ? (
            <ContentSeoActionBar projectId={projectId} onFeedback={setFeedback} />
          ) : undefined
        }
      />

      <nav className="content-seo-tabs" aria-label="Sezioni Content SEO">
        {MAIN_TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`content-seo-tabs__btn ${tab === t.id ? "content-seo-tabs__btn--active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "products" && (
        <>
          {!connected && (
            <div className="gcr-card gcr-card--glow content-seo-connect-card">
              <p className="gcr-card__label">Shopify richiesto</p>
              <h3 className="gcr-card__title">Collega Shopify per iniziare</h3>
              <p className="gcr-card__description">
                Sincronizza prodotti (Sync v2) e categorie, poi analizza e genera proposte SEO revisionabili.
              </p>
              {id && (
                <Link
                  to={APP_ROUTES.projectIntegrations(id)}
                  className="gcr-btn gcr-btn--primary gcr-btn--sm"
                >
                  Vai alle integrazioni
                </Link>
              )}
            </div>
          )}

          {connected && (
            <SeoOptimizerRoom
              projectId={projectId}
              connected={connected}
              feedback={feedback}
              onDismissFeedback={() => setFeedback(null)}
            />
          )}
        </>
      )}

      {tab === "editorial" && (
        <ContentSeoEditorialRoom projectId={projectId} shopifyConnected={connected} />
      )}
    </motion.div>
  );
}
