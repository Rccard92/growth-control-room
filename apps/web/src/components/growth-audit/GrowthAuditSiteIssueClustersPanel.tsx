import {
  getGrowthAuditFindingSeverityLabel,
  getGrowthAuditSeverityBadgeClass,
  type GrowthAuditSiteIssueCluster,
} from "../../lib/growth-audit-utils";

interface GrowthAuditSiteIssueClustersPanelProps {
  clusters: GrowthAuditSiteIssueCluster[];
  maxItems?: number;
}

export function GrowthAuditSiteIssueClustersPanel({
  clusters,
  maxItems = 8,
}: GrowthAuditSiteIssueClustersPanelProps) {
  const topClusters = clusters.slice(0, maxItems);

  if (topClusters.length === 0) {
    return (
      <section className="growth-audit-issue-clusters">
        <h3 className="growth-audit-issue-clusters__title">Problemi ricorrenti</h3>
        <p className="growth-audit-issue-clusters__empty">
          Nessun cluster di problemi aperti rilevato sul sito.
        </p>
      </section>
    );
  }

  return (
    <section className="growth-audit-issue-clusters">
      <h3 className="growth-audit-issue-clusters__title">Problemi ricorrenti</h3>
      <ul className="growth-audit-issue-clusters__list">
        {topClusters.map((cluster) => (
          <li key={cluster.key} className="growth-audit-issue-cluster-card gcr-card">
            <div className="growth-audit-issue-cluster-card__meta">
              <span className={getGrowthAuditSeverityBadgeClass(cluster.severity)}>
                {getGrowthAuditFindingSeverityLabel(cluster.severity)}
              </span>
              <span className="growth-audit-issue-cluster-card__category">{cluster.category}</span>
              <span className="growth-audit-issue-cluster-card__count">
                {cluster.count} {cluster.count === 1 ? "occorrenza" : "occorrenze"}
              </span>
            </div>
            <h4 className="growth-audit-issue-cluster-card__title">{cluster.title}</h4>
            <p className="growth-audit-issue-cluster-card__pages">
              {cluster.affectedPageIds.length}{" "}
              {cluster.affectedPageIds.length === 1 ? "pagina impattata" : "pagine impattate"}
            </p>
            <p className="growth-audit-issue-cluster-card__recommendation">
              {cluster.recommendation}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
