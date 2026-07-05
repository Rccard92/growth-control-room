import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useParams, useSearchParams } from "react-router-dom";
import { INTEGRATIONS } from "@gcr/shared";
import { GoogleIntegrationCard } from "../components/GoogleIntegrationCard";
import { IntegrationCard } from "../components/IntegrationCard";
import { IntegrationGraph } from "../components/IntegrationGraph";
import { PageHeader } from "../components/PageHeader";
import {
  useGoogleIntegrationStatus,
  useStartGoogleOAuth,
} from "../hooks/useGoogleIntegrations";
import { useProject, useProjectIntegrations } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";

export function IntegrationsPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const { data: project } = useProject(id);
  const { data: integrations, isLoading, error } = useProjectIntegrations(id);
  const { data: googleStatus, isLoading: isGoogleLoading } = useGoogleIntegrationStatus(id);
  const startGoogleOAuth = useStartGoogleOAuth(id);
  const [banner, setBanner] = useState<{ type: "success" | "error"; message: string } | null>(
    null,
  );

  const statusMap = useMemo(
    () => new Map((integrations ?? []).map((integration) => [integration.provider, integration.status])),
    [integrations],
  );

  useEffect(() => {
    if (searchParams.get("google_connected") === "1") {
      setBanner({
        type: "success",
        message: "Account Google collegato correttamente.",
      });
      searchParams.delete("google_connected");
      setSearchParams(searchParams, { replace: true });
    } else if (searchParams.get("google_error")) {
      setBanner({
        type: "error",
        message: "Collegamento Google non completato. Riprova.",
      });
      searchParams.delete("google_error");
      setSearchParams(searchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const handleConnectGoogle = async () => {
    const response = await startGoogleOAuth.mutateAsync({
      services: ["search_console", "analytics", "google_ads"],
    });
    window.location.href = response.authorizationUrl;
  };

  const oauthConnectDisabled =
    startGoogleOAuth.isPending || googleStatus?.oauth.status === "missing_credentials";

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="Integration Center"
        subtitle="Collega le piattaforme e-commerce e marketing al progetto"
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "Integrazioni" },
        ]}
      />

      {banner && (
        <div
          className={`gcr-alert ${banner.type === "success" ? "gcr-alert--success" : "gcr-alert--error"}`}
          style={{ marginBottom: "1rem" }}
        >
          {banner.message}
        </div>
      )}

      {isLoading && <div className="gcr-skeleton" style={{ height: 120 }} />}
      {error && <div className="gcr-alert gcr-alert--error">{error.message}</div>}

      <div className="gcr-grid gcr-grid--auto" style={{ marginBottom: "2rem" }}>
        {INTEGRATIONS.map((meta) => {
          const isShopify = meta.provider === "shopify";
          const apiStatus = statusMap.get(meta.provider);

          if (isShopify) {
            const connected = apiStatus === "connected";
            return (
              <IntegrationCard
                key={meta.provider}
                meta={meta}
                status={apiStatus ?? "not_connected"}
                href={
                  connected
                    ? APP_ROUTES.projectShopify(id!)
                    : APP_ROUTES.projectShopifyConnect(id!)
                }
                actionLabel={connected ? "Gestisci" : "Connetti"}
              />
            );
          }

          return (
            <IntegrationCard
              key={meta.provider}
              meta={meta}
              status="coming_soon"
              actionLabel="Coming soon"
              disabled
            />
          );
        })}
      </div>

      <section className="google-integrations-section">
        <h2 className="google-integrations-section__title">Google Data Sources</h2>
        <p className="google-integrations-section__subtitle">
          Stato delle integrazioni Google per performance, SEO e advertising.
        </p>

        {isGoogleLoading && <div className="gcr-skeleton" style={{ height: 120 }} />}

        {googleStatus && (
          <div className="google-integrations-section__grid">
            <GoogleIntegrationCard
              title="PageSpeed Insights"
              description="Performance e Lighthouse lab data per le pagine prioritarie."
              icon="⚡"
              status={googleStatus.pagespeed}
            />
            <GoogleIntegrationCard
              title="Chrome UX Report"
              description="Core Web Vitals real-user per capire l'esperienza reale."
              icon="📊"
              status={googleStatus.crux}
            />
            <GoogleIntegrationCard
              title="Search Console"
              description="Query, CTR, posizionamento e indicizzazione."
              icon="🔎"
              status={googleStatus.searchConsole}
              actionLabel="Collega Google"
              onAction={() => void handleConnectGoogle()}
              disabled={oauthConnectDisabled}
            />
            <GoogleIntegrationCard
              title="Google Analytics 4"
              description="Traffico, conversioni e priorità economiche."
              icon="📈"
              status={googleStatus.analytics}
              actionLabel="Collega Google"
              onAction={() => void handleConnectGoogle()}
              disabled={oauthConnectDisabled}
            />
            <GoogleIntegrationCard
              title="Google Ads"
              description="Landing ads e priorità economiche per campagne."
              icon="🎯"
              status={googleStatus.googleAds}
              actionLabel={
                googleStatus.googleAds.status === "setup_incomplete"
                  ? "Configura token Google Ads"
                  : "Collega Google"
              }
              onAction={() => void handleConnectGoogle()}
              disabled={
                oauthConnectDisabled || googleStatus.googleAds.status === "setup_incomplete"
              }
              note={
                googleStatus.googleAds.status === "setup_incomplete"
                  ? "Developer Token mancante"
                  : undefined
              }
            />
          </div>
        )}
      </section>

      <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--gcr-text)", marginBottom: "1rem" }}>
        Integration Graph
      </h2>
      <p style={{ fontSize: "0.8125rem", color: "var(--gcr-text-muted)", marginBottom: "1rem" }}>
        Vista relazionale del progetto e dei connettori. Shopify è il primo provider attivo.
      </p>
      {integrations && (
        <IntegrationGraph
          projectName={project?.name ?? "Progetto"}
          integrations={integrations}
        />
      )}
    </motion.div>
  );
}
