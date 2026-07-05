import { useMemo, type CSSProperties } from "react";
import {
  Background,
  Controls,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import {
  INTEGRATIONS,
  type GoogleIntegrationStatusResponse,
  type GoogleServiceStatusValue,
  type Integration,
  type IntegrationProvider,
} from "@gcr/shared";

export type IntegrationGraphNodeStatus =
  | "connected"
  | "not_connected"
  | "needs_setup"
  | "missing_credentials"
  | "setup_incomplete"
  | "coming_soon"
  | "error";

interface IntegrationGraphProps {
  projectName: string;
  integrations: Integration[];
  googleStatus?: GoogleIntegrationStatusResponse;
  searchConsoleSiteUrl?: string | null;
}

const PROVIDER_POSITIONS: Record<string, { x: number; y: number }> = {
  shopify: { x: 0, y: -120 },
  meta_ads: { x: 120, y: -60 },
  google_ads: { x: 170, y: 40 },
  klaviyo: { x: 120, y: 140 },
  ga4: { x: 0, y: 170 },
  google_search_console: { x: -120, y: 140 },
  merchant_center: { x: -170, y: 40 },
  tiktok_ads: { x: -120, y: -60 },
  google_pagespeed: { x: 230, y: 110 },
  google_crux: { x: 230, y: 180 },
};

function mapGoogleServiceToGraphStatus(
  status: GoogleServiceStatusValue | undefined,
): IntegrationGraphNodeStatus {
  if (!status) return "coming_soon";
  if (status === "connected") return "connected";
  if (status === "setup_incomplete") return "setup_incomplete";
  if (status === "missing_credentials") return "missing_credentials";
  if (status === "needs_setup") return "needs_setup";
  return "not_connected";
}

export function getProviderGraphStatus(
  provider: IntegrationProvider,
  statusMap: Map<string, string>,
  googleStatus?: GoogleIntegrationStatusResponse,
): IntegrationGraphNodeStatus {
  switch (provider) {
    case "shopify":
      return (statusMap.get(provider) as IntegrationGraphNodeStatus | undefined) ?? "not_connected";
    case "google_search_console":
      return mapGoogleServiceToGraphStatus(googleStatus?.searchConsole.status);
    case "ga4":
      return mapGoogleServiceToGraphStatus(googleStatus?.analytics.status);
    case "google_ads":
      return mapGoogleServiceToGraphStatus(googleStatus?.googleAds.status);
    case "google_pagespeed":
      return mapGoogleServiceToGraphStatus(googleStatus?.pagespeed.status);
    case "google_crux":
      return mapGoogleServiceToGraphStatus(googleStatus?.crux.status);
    default:
      return statusMap.has(provider)
        ? ((statusMap.get(provider) as IntegrationGraphNodeStatus) ?? "not_connected")
        : "coming_soon";
  }
}

export function buildProviderGraphLabel(
  label: string,
  status: IntegrationGraphNodeStatus,
): string {
  if (status === "coming_soon") return `${label} 🔒`;
  if (status === "setup_incomplete") return `${label} ⚠`;
  return label;
}

function nodeStyle(status: IntegrationGraphNodeStatus, isShopify: boolean): CSSProperties {
  const base: CSSProperties = {
    padding: "10px 14px",
    borderRadius: 10,
    fontSize: 12,
    fontWeight: 600,
    border: "1px solid var(--gcr-border)",
    background: "var(--gcr-surface)",
    color: "var(--gcr-text-muted)",
    minWidth: 100,
    textAlign: "center",
  };

  if (isShopify && status === "connected") {
    return {
      ...base,
      borderColor: "rgba(34, 211, 238, 0.4)",
      background: "var(--gcr-accent-cyan-dim)",
      color: "var(--gcr-accent-cyan)",
      boxShadow: "var(--gcr-glow-cyan)",
    };
  }
  if (status === "connected") {
    return {
      ...base,
      borderColor: "rgba(52, 211, 153, 0.35)",
      background: "var(--gcr-success-dim)",
      color: "var(--gcr-success)",
    };
  }
  if (status === "setup_incomplete" || status === "missing_credentials") {
    return {
      ...base,
      borderColor: "rgba(237, 180, 99, 0.45)",
      background: "rgba(237, 180, 99, 0.12)",
      color: "rgba(237, 180, 99, 0.95)",
    };
  }
  if (status === "coming_soon") {
    return { ...base, opacity: 0.45 };
  }
  return base;
}

function edgeStyle(status: IntegrationGraphNodeStatus, isShopify: boolean): {
  stroke: string;
  strokeWidth: number;
  animated: boolean;
} {
  if (status === "connected") {
    return {
      stroke: isShopify ? "var(--gcr-accent-cyan)" : "var(--gcr-success)",
      strokeWidth: isShopify ? 2 : 2,
      animated: true,
    };
  }
  if (status === "setup_incomplete" || status === "missing_credentials") {
    return {
      stroke: "rgba(237, 180, 99, 0.75)",
      strokeWidth: 2,
      animated: false,
    };
  }
  return {
    stroke: "var(--gcr-border)",
    strokeWidth: 1,
    animated: false,
  };
}

export function IntegrationGraph({
  projectName,
  integrations,
  googleStatus,
}: IntegrationGraphProps) {
  const statusMap = useMemo(
    () => new Map(integrations.map((i) => [i.provider, i.status])),
    [integrations],
  );

  const { nodes, edges } = useMemo(() => {
    const centerId = "project";
    const graphNodes: Node[] = [
      {
        id: centerId,
        data: { label: projectName },
        position: { x: 0, y: 0 },
        style: {
          padding: "14px 20px",
          borderRadius: 12,
          fontSize: 13,
          fontWeight: 700,
          border: "1px solid rgba(139, 92, 246, 0.4)",
          background: "var(--gcr-accent-violet-dim)",
          color: "var(--gcr-text)",
          boxShadow: "var(--gcr-glow-violet)",
        },
      },
    ];

    const graphEdges: Edge[] = [];

    for (const integration of INTEGRATIONS) {
      const provider = integration.provider;
      const status = getProviderGraphStatus(provider, statusMap, googleStatus);
      const pos = PROVIDER_POSITIONS[provider] ?? { x: 0, y: 0 };
      const nodeId = provider;
      const edge = edgeStyle(status, provider === "shopify");

      graphNodes.push({
        id: nodeId,
        data: {
          label: buildProviderGraphLabel(integration.label, status),
        },
        position: pos,
        style: nodeStyle(status, provider === "shopify"),
      });

      graphEdges.push({
        id: `${centerId}-${nodeId}`,
        source: centerId,
        target: nodeId,
        animated: edge.animated,
        style: {
          stroke: edge.stroke,
          strokeWidth: edge.strokeWidth,
        },
      });
    }

    return { nodes: graphNodes, edges: graphEdges };
  }, [projectName, statusMap, googleStatus]);

  return (
    <div className="gcr-graph-wrap">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="var(--gcr-border)" gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
