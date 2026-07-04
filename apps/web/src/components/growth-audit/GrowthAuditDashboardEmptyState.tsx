interface GrowthAuditDashboardEmptyStateProps {
  variant: "no-run" | "no-pages";
}

export function GrowthAuditDashboardEmptyState({
  variant,
}: GrowthAuditDashboardEmptyStateProps) {
  return (
    <div className="growth-audit-dashboard-empty gcr-card">
      {variant === "no-run" ? (
        <p>Avvia un Full Site Audit per vedere le priorità.</p>
      ) : (
        <p>Nessuna pagina disponibile.</p>
      )}
    </div>
  );
}
