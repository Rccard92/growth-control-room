import { motion } from "framer-motion";
import { useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
} from "recharts";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { useProject } from "../hooks/useProjects";
import { APP_ROUTES } from "../routes/config";

const ANOMALY_DATA = [
  { day: "Lun", value: 2 },
  { day: "Mar", value: 5 },
  { day: "Mer", value: 3 },
  { day: "Gio", value: 8 },
  { day: "Ven", value: 4 },
  { day: "Sab", value: 6 },
  { day: "Dom", value: 1 },
];

const BLOCKS = [
  {
    title: "Daily Brief",
    content: "Nessun brief generato oggi. Collega integrazioni e sincronizza dati per attivare l'analisi AI automatica del progetto.",
  },
  {
    title: "Anomalie",
    content: "Monitoraggio anomalie su revenue, conversion rate e spesa ads — in attesa di dati sufficienti.",
  },
  {
    title: "Opportunità",
    content: "Identificazione opportunità di crescita cross-channel basata su performance storica e benchmark di settore.",
  },
  {
    title: "Prossime azioni consigliate",
    items: [
      "Collega Shopify e sincronizza ordini/prodotti",
      "Configura Google Search Console (coming soon)",
      "Attiva il daily brief AI dopo la prima sync",
    ],
  },
];

export function AiBriefPage() {
  const { id } = useParams<{ id: string }>();
  const { data: project } = useProject(id);

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <PageHeader
        title="AI Brief"
        subtitle="Analisi e raccomandazioni generate dall'AI analyst"
        breadcrumb={[
          { label: "Progetti", href: APP_ROUTES.projects },
          { label: project?.name ?? id ?? "", href: id ? APP_ROUTES.project(id) : undefined },
          { label: "AI Brief" },
        ]}
      />

      <div className="gcr-grid gcr-grid--2" style={{ marginBottom: "1.5rem" }}>
        {BLOCKS.slice(0, 3).map((block) => (
          <div key={block.title} className="gcr-card">
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.75rem" }}>
              <p className="gcr-card__label" style={{ margin: 0 }}>{block.title}</p>
              <StatusBadge variant="coming_soon" label="Preview" />
            </div>
            <p style={{ fontSize: "0.875rem", color: "var(--gcr-text-muted)", margin: 0, lineHeight: 1.6 }}>
              {block.content}
            </p>
          </div>
        ))}

        <div className="gcr-card">
          <p className="gcr-card__label">Anomalie — trend settimanale</p>
          <div style={{ height: 160, marginTop: "0.5rem" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ANOMALY_DATA}>
                <XAxis dataKey="day" stroke="var(--gcr-text-dim)" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    background: "var(--gcr-bg-elevated)",
                    border: "1px solid var(--gcr-border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="value" fill="var(--gcr-accent-violet)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="gcr-card">
        <p className="gcr-card__label">{BLOCKS[3].title}</p>
        <ul style={{ margin: "0.75rem 0 0", paddingLeft: "1.25rem", fontSize: "0.875rem", color: "var(--gcr-text-muted)", lineHeight: 1.8 }}>
          {BLOCKS[3].items?.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
}
