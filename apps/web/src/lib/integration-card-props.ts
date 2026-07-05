import type {
  GoogleIntegrationStatusResponse,
  GoogleServiceStatus,
  IntegrationMeta,
  IntegrationStatus,
  IntegrationUiStatus,
} from "@gcr/shared";
import type { IntegrationCardProps } from "../components/IntegrationCard";
import { APP_ROUTES } from "../routes/config";

interface GetIntegrationCardPropsInput {
  meta: IntegrationMeta;
  apiStatus?: IntegrationStatus;
  googleStatus?: GoogleIntegrationStatusResponse;
  oauthConnectDisabled: boolean;
  handleConnectGoogle: () => void;
  projectId: string;
  searchConsoleSiteUrl?: string | null;
  onSelectSearchConsoleProperty?: () => void;
  googleAnalyticsPropertyId?: string | null;
  googleAnalyticsPropertyName?: string | null;
  onSelectGoogleAnalyticsProperty?: () => void;
}

function mapGoogleStatus(status: GoogleServiceStatus["status"]): IntegrationUiStatus {
  return status;
}

function apiKeyCardProps(
  meta: IntegrationMeta,
  service: GoogleServiceStatus,
  missingEnvNote: string,
): IntegrationCardProps {
  const status = mapGoogleStatus(service.status);

  if (status === "connected") {
    return {
      meta,
      status,
      badgeLabel: "Configurata",
      actionLabel: "Configurata",
      disabled: true,
    };
  }

  return {
    meta,
    status: "missing_credentials",
    badgeLabel: "Mancante",
    actionLabel: "Configura API key",
    disabled: true,
    note: missingEnvNote,
  };
}

function oauthCardProps(
  meta: IntegrationMeta,
  service: GoogleServiceStatus,
  oauthConnectDisabled: boolean,
  handleConnectGoogle: () => void,
  options?: {
    setupIncompleteNote?: string;
    setupIncompleteActionLabel?: string;
  },
): IntegrationCardProps {
  const status = mapGoogleStatus(service.status);

  if (status === "connected") {
    return {
      meta,
      status,
      badgeLabel: "Collegata",
      actionLabel: "Collegata",
      disabled: true,
    };
  }

  if (status === "setup_incomplete") {
    return {
      meta,
      status,
      actionLabel: options?.setupIncompleteActionLabel ?? "Developer Token mancante",
      disabled: true,
      note: options?.setupIncompleteNote ?? "Aggiungi GOOGLE_ADS_DEVELOPER_TOKEN su Railway",
    };
  }

  if (status === "missing_credentials") {
    return {
      meta,
      status,
      actionLabel: "OAuth mancante",
      disabled: true,
    };
  }

  return {
    meta,
    status,
    actionLabel: "Collega Google",
    onAction: handleConnectGoogle,
    disabled: oauthConnectDisabled,
  };
}

export function getIntegrationCardProps({
  meta,
  apiStatus,
  googleStatus,
  oauthConnectDisabled,
  handleConnectGoogle,
  projectId,
  searchConsoleSiteUrl,
  onSelectSearchConsoleProperty,
  googleAnalyticsPropertyId,
  googleAnalyticsPropertyName,
  onSelectGoogleAnalyticsProperty,
}: GetIntegrationCardPropsInput): IntegrationCardProps {
  if (meta.provider === "shopify") {
    const connected = apiStatus === "connected";
    return {
      meta,
      status: apiStatus ?? "not_connected",
      href: connected
        ? APP_ROUTES.projectShopify(projectId)
        : APP_ROUTES.projectShopifyConnect(projectId),
      actionLabel: connected ? "Gestisci" : "Connetti",
    };
  }

  if (!googleStatus) {
    return {
      meta,
      status: "not_connected",
      actionLabel: "Caricamento...",
      disabled: true,
    };
  }

  switch (meta.provider) {
    case "google_pagespeed":
      return apiKeyCardProps(
        meta,
        googleStatus.pagespeed,
        "GOOGLE_PAGESPEED_API_KEY mancante",
      );
    case "google_crux":
      return apiKeyCardProps(meta, googleStatus.crux, "GOOGLE_CRUX_API_KEY mancante");
    case "google_search_console": {
      const base = oauthCardProps(
        meta,
        googleStatus.searchConsole,
        oauthConnectDisabled,
        handleConnectGoogle,
      );
      if (googleStatus.searchConsole.status !== "connected") {
        return base;
      }
      return {
        ...base,
        secondaryActionLabel: searchConsoleSiteUrl ? "Modifica proprietà" : "Seleziona proprietà",
        onSecondaryAction: onSelectSearchConsoleProperty,
        detailText: searchConsoleSiteUrl ? `Proprietà: ${searchConsoleSiteUrl}` : undefined,
      };
    }
    case "ga4": {
      const base = oauthCardProps(
        meta,
        googleStatus.analytics,
        oauthConnectDisabled,
        handleConnectGoogle,
      );
      if (googleStatus.analytics.status !== "connected") {
        return base;
      }
      return {
        ...base,
        secondaryActionLabel: googleAnalyticsPropertyId ? "Modifica proprietà" : "Seleziona proprietà",
        onSecondaryAction: onSelectGoogleAnalyticsProperty,
        detailText: googleAnalyticsPropertyName
          ? `Proprietà: ${googleAnalyticsPropertyName}`
          : undefined,
      };
    }
    case "google_ads":
      return oauthCardProps(
        meta,
        googleStatus.googleAds,
        oauthConnectDisabled,
        handleConnectGoogle,
        {
          setupIncompleteActionLabel: "Developer Token mancante",
          setupIncompleteNote: "Aggiungi GOOGLE_ADS_DEVELOPER_TOKEN su Railway",
        },
      );
    default:
      return {
        meta,
        status: "coming_soon",
        actionLabel: "Coming soon",
        disabled: true,
      };
  }
}
