import type { GrowthAuditTask } from "@gcr/shared";
import {
  getGrowthAuditOwnerTypeLabel,
  getGrowthAuditTaskPriorityLabel,
} from "../../lib/growth-audit-utils";

interface GrowthAuditPageTasksPanelProps {
  tasks: GrowthAuditTask[];
}

export function GrowthAuditPageTasksPanel({ tasks }: GrowthAuditPageTasksPanelProps) {
  return (
    <section className="growth-audit-page-drawer__section">
      <h4 className="growth-audit-page-drawer__section-title">Task</h4>
      {tasks.length === 0 ? (
        <p className="growth-audit-page-drawer__empty">
          Nessun task tecnico aperto per questa pagina.
        </p>
      ) : (
        <ul className="growth-audit-page-tasks">
          {tasks.map((task) => (
            <li key={task.id} className="growth-audit-page-task">
              <div className="growth-audit-page-task__meta">
                <span className="growth-audit-page-task__priority">
                  {getGrowthAuditTaskPriorityLabel(task.priority)}
                </span>
                <span className="growth-audit-page-task__owner">
                  {getGrowthAuditOwnerTypeLabel(task.ownerType)}
                </span>
                <span className="growth-audit-page-task__effort">{task.estimatedEffort}</span>
              </div>
              <strong className="growth-audit-page-task__title">{task.title}</strong>
              {task.description && (
                <p className="growth-audit-page-task__description">{task.description}</p>
              )}
            </li>
          ))}
        </ul>
      )}
      <p className="growth-audit-page-tasks__note">
        Questi task sono generati dalla scansione tecnica. Negli step successivi verranno
        arricchiti con AI/GEO/CRO.
      </p>
    </section>
  );
}
