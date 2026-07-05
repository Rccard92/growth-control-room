import { useMemo, type CSSProperties } from "react";
import {
  Background,
  Controls,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import { INTEGRATIONS, type Integration } from "@gcr/shared";

interface IntegrationGraphProps {
  projectName: string;
  integrations: Integration[];
}

const GRAPH_PROVIDERS = INTEGRATIONS.filter(
  (integration) =>
    integration.provider !== "google_pagespeed" && integration.provider !== "google_crux",
);

const PROVIDER_POSITIONS: Record<string, { x: number; y: number }> = {
  shopify: { x: 0, y: -120 },
  meta_ads: { x: 120, y: -60 },
  google_ads: { x: 170, y: 40 },
  klaviyo: { x: 120, y: 140 },
  ga4: { x: 0, y: 170 },
  google_search_console: { x: -120, y: 140 },
  merchant_center: { x: -170, y: 40 },
  tiktok_ads: { x: -120, y: -60 },
};

function nodeStyle(
  status: string,
  isShopify: boolean,
): CSSProperties {
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

  if (isShopify && status !== "coming_soon") {
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
  if (status === "coming_soon") {
    return { ...base, opacity: 0.45 };
  }
  return base;
}

export function IntegrationGraph({ projectName, integrations }: IntegrationGraphProps) {
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

    for (const integration of GRAPH_PROVIDERS) {
      const provider = integration.provider;
      const apiStatus = statusMap.get(provider);
      const status =
        provider === "shopify"
          ? apiStatus ?? "not_connected"
          : "coming_soon";
      const pos = PROVIDER_POSITIONS[provider] ?? { x: 0, y: 0 };
      const nodeId = provider;

      graphNodes.push({
        id: nodeId,
        data: {
          label: status === "coming_soon" ? `${integration.label} 🔒` : integration.label,
        },
        position: pos,
        style: nodeStyle(status, provider === "shopify"),
      });

      graphEdges.push({
        id: `${centerId}-${nodeId}`,
        source: centerId,
        target: nodeId,
        animated: provider === "shopify" && status === "connected",
        style: {
          stroke: provider === "shopify" ? "var(--gcr-accent-cyan)" : "var(--gcr-border)",
          strokeWidth: provider === "shopify" ? 2 : 1,
        },
      });
    }

    return { nodes: graphNodes, edges: graphEdges };
  }, [projectName, statusMap]);

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
