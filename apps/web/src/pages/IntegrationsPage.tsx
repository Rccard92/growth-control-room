import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { useParams, useSearchParams } from "react-router-dom";
import { INTEGRATIONS } from "@gcr/shared";
import { IntegrationCard } from "../components/IntegrationCard";
import { GoogleSearchConsolePropertyModal } from "../components/integrations/GoogleSearchConsolePropertyModal";
import { IntegrationGraph } from "../components/IntegrationGraph";
import { PageHeader } from "../components/PageHeader";
import {
  useGoogleIntegrationStatus,
  useStartGoogleOAuth,
} from "../hooks/useGoogleIntegrations";
import { getIntegrationCardProps } from "../lib/integration-card-props";
import { useProject, useProjectIntegrations } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";

export function IntegrationsPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const { data: project } = useProject(id);
  const { data: integrations, isLoading, error } = useProjectIntegrations(id);
  const { data: googleStatus, isLoading: isGoogleLoading } = useGoogleIntegrationStatus(id);
  const startGoogleOAuth = useStartGoogleOAuth(id);
  const [isSearchConsoleModalOpen, setIsSearchConsoleModalOpen] = useState(false);
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
        message: "Collegamento Google non completato. Se hai appena autorizzato l'account, attendi il deploy del fix e riprova.",
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

  const isGridLoading = isLoading || isGoogleLoading;

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="Integration Center"
        subtitle="Collega e monitora le fonti dati del progetto."
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

      {error && <div className="gcr-alert gcr-alert--error">{error.message}</div>}

      <p className="integrations-page__hint">
        Le fonti Google usano API key per PageSpeed/CrUX e OAuth per Search Console, GA4 e Ads.
      </p>

      {isGridLoading && <div className="gcr-skeleton" style={{ height: 120 }} />}

      {!isGridLoading && id && (
        <div className="gcr-grid gcr-grid--auto" style={{ marginBottom: "2rem" }}>
          {INTEGRATIONS.map((meta) => (
            <IntegrationCard
              key={meta.provider}
              {...getIntegrationCardProps({
                meta,
                apiStatus: statusMap.get(meta.provider),
                googleStatus,
                oauthConnectDisabled,
                handleConnectGoogle: () => void handleConnectGoogle(),
                projectId: id,
                searchConsoleSiteUrl: project?.searchConsoleSiteUrl,
                onSelectSearchConsoleProperty: () => setIsSearchConsoleModalOpen(true),
              })}
            />
          ))}
        </div>
      )}

      {id && (
        <GoogleSearchConsolePropertyModal
          projectId={id}
          selectedSiteUrl={project?.searchConsoleSiteUrl}
          open={isSearchConsoleModalOpen}
          onClose={() => setIsSearchConsoleModalOpen(false)}
        />
      )}

      <h2 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--gcr-text)", marginBottom: "1rem" }}>
        Integration Graph
      </h2>
      <p style={{ fontSize: "0.8125rem", color: "var(--gcr-text-muted)", marginBottom: "1rem" }}>
        Vista relazionale delle fonti dati collegate al progetto.
      </p>
      {integrations && (
        <IntegrationGraph
          projectName={project?.name ?? "Progetto"}
          integrations={integrations}
          googleStatus={googleStatus}
          searchConsoleSiteUrl={project?.searchConsoleSiteUrl}
        />
      )}
    </motion.div>
  );
}
