import type { SeoSkillTaskView } from "./seo-skills-utils";

interface SeoSkillTasksListProps {
  tasks: SeoSkillTaskView[];
}

export function SeoSkillTasksList({ tasks }: SeoSkillTasksListProps) {
  if (!tasks.length) {
    return <p className="seo-skill-result-section__empty">Nessun task operativo.</p>;
  }

  return (
    <ul className="seo-skill-tasks-list">
      {tasks.map((task, index) => (
        <li
          key={`${task.title}-${index}`}
          className={`seo-skill-task ${
            task.priority === "high" ? "seo-skill-task--priority-high" : ""
          }`}
        >
          <h5 className="seo-skill-task__title">{task.title}</h5>
          {task.description && <p className="seo-skill-task__description">{task.description}</p>}
          <div className="seo-skill-task__meta">
            <span>Priorità: {task.priorityLabel}</span>
            <span>Owner: {task.ownerTypeLabel}</span>
            <span>Sforzo: {task.estimatedEffortLabel}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}
