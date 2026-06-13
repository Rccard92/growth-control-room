import { motion } from "framer-motion";

export function averageScore(items: { score?: number | null }[]): number | null {
  const scored = items.map((i) => i.score).filter((s): s is number => s != null);
  if (!scored.length) return null;
  return Math.round(scored.reduce((a, b) => a + b, 0) / scored.length);
}

function scoreToneClass(value: number | null): string {
  if (value == null) return "";
  if (value >= 80) return "content-seo-kpi__value--good";
  if (value >= 60) return "content-seo-kpi__value--warn";
  return "content-seo-kpi__value--critical";
}

interface KpiCardProps {
  label: string;
  value: string | number;
  toneClass?: string;
  index: number;
}

function KpiCard({ label, value, toneClass = "", index }: KpiCardProps) {
  return (
    <motion.div
      className="content-seo-kpi gcr-card content-seo-kpi--compact"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.04 }}
    >
      <span className={`content-seo-kpi__value ${toneClass}`}>{value}</span>
      <span className="content-seo-kpi__label">{label}</span>
    </motion.div>
  );
}

interface ContentSeoOptimizerKpiProps {
  productsCount: number;
  averageProductScore: number | null;
  collectionsCount: number;
  averageCollectionScore: number | null;
  criticalIssues: number;
  missingFieldsCount: number;
  loading?: boolean;
}

export function ContentSeoOptimizerKpi({
  productsCount,
  averageProductScore,
  collectionsCount,
  averageCollectionScore,
  criticalIssues,
  missingFieldsCount,
  loading,
}: ContentSeoOptimizerKpiProps) {
  if (loading) {
    return (
      <div className="content-seo-kpi-strip content-seo-kpi-strip--compact">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="gcr-skeleton content-seo-kpi-skeleton" />
        ))}
      </div>
    );
  }

  return (
    <div className="content-seo-kpi-strip content-seo-kpi-strip--compact">
      <KpiCard label="Prodotti" value={productsCount} index={0} />
      <KpiCard
        label="Score medio prodotti"
        value={averageProductScore ?? "—"}
        toneClass={scoreToneClass(averageProductScore)}
        index={1}
      />
      <KpiCard label="Categorie" value={collectionsCount} index={2} />
      <KpiCard
        label="Score medio categorie"
        value={averageCollectionScore ?? "—"}
        toneClass={scoreToneClass(averageCollectionScore)}
        index={3}
      />
      <KpiCard
        label="Criticità aperte"
        value={criticalIssues}
        toneClass={criticalIssues > 0 ? "content-seo-kpi__value--critical" : ""}
        index={4}
      />
      <KpiCard
        label="Campi mancanti"
        value={missingFieldsCount}
        toneClass={missingFieldsCount > 0 ? "content-seo-kpi__value--warn" : ""}
        index={5}
      />
    </div>
  );
}
