import { Link, useParams } from "react-router-dom";
import { useAiBudgetStatus } from "../../hooks/useAiUsage";
import { APP_ROUTES } from "../../routes/config";

export function AiBudgetBanner() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? "";
  const { data } = useAiBudgetStatus(projectId);

  if (!projectId || !data?.nearLimit) return null;

  return (
    <div
      className={`gcr-alert ${data.blocked ? "gcr-alert--error" : "gcr-alert--warning"} ai-budget-banner`}
    >
      {data.blocked ? (
        <span>Budget AI superato — nuove generazioni bloccate.</span>
      ) : (
        <span>Budget AI quasi esaurito.</span>
      )}{" "}
      <Link to={APP_ROUTES.projectAiCosts(projectId)}>Vai ad AI Costs</Link>
    </div>
  );
}
