import { useEffect, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import type { EditorialBriefBatchJobResponse } from "@gcr/shared";
import { AppModal } from "../../ui/AppModal";
import { getEditorialBriefBatchJob } from "../../../lib/content-api";
import { queryKeys } from "../../../lib/queryKeys";

interface EditorialBatchBriefModalProps {
  open: boolean;
  projectId: string;
  jobId: string | null;
  onClose: () => void;
  onComplete?: () => void;
}

function isRunning(status: string): boolean {
  return status === "pending" || status === "running";
}

function completionMessage(job: EditorialBriefBatchJobResponse): string {
  if (job.status === "completed") {
    return `Brief generati: ${job.completedItems} completati, 0 falliti.`;
  }
  if (job.status === "partial_failed") {
    return `Generazione parziale: ${job.completedItems} completati, ${job.failedItems} falliti.`;
  }
  if (job.status === "failed") {
    return "Generazione non riuscita per tutti i contenuti selezionati.";
  }
  return "";
}

export function EditorialBatchBriefModal({
  open,
  projectId,
  jobId,
  onClose,
  onComplete,
}: EditorialBatchBriefModalProps) {
  const qc = useQueryClient();

  const jobQuery = useQuery({
    queryKey: queryKeys.contentSeo.editorialBriefJob(projectId, jobId ?? ""),
    queryFn: () => getEditorialBriefBatchJob(projectId, jobId!),
    enabled: open && Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status && isRunning(status)) return 2000;
      return false;
    },
  });

  const job = jobQuery.data;
  const done = job && !isRunning(job.status);

  useEffect(() => {
    if (!done || !job) return;
    void qc.invalidateQueries({ queryKey: ["contentSeo", projectId, "editorialItems"] });
    onComplete?.();
  }, [done, job, onComplete, projectId, qc]);

  const progressLabel = useMemo(() => {
    if (!job) return "";
    if (job.currentItemTitle && isRunning(job.status)) {
      return `Elaborazione: ${job.currentItemTitle}`;
    }
    return "";
  }, [job]);

  const footer = (
    <button type="button" className="gcr-btn gcr-btn--secondary" onClick={onClose}>
      {done ? "Chiudi" : "Chiudi (job in background)"}
    </button>
  );

  return (
    <AppModal
      open={open}
      onClose={onClose}
      title="Generazione brief in corso"
      subtitle="I brief vengono creati uno alla volta con Brand Intelligence."
      maxWidth="sm"
      footer={footer}
    >
      <div className="editorial-batch-progress">
        {jobQuery.isError && (
          <div className="gcr-alert gcr-alert--error">
            Impossibile avviare la generazione massiva. Riprova più tardi.
          </div>
        )}

        {job && (
          <>
            <div className="editorial-batch-progress__stats">
              <span>
                {job.completedItems + job.failedItems} / {job.totalItems}
              </span>
              <span>{job.progressPercent}%</span>
            </div>
            <div className="editorial-batch-progress__bar" aria-hidden>
              <div
                className="editorial-batch-progress__bar-fill"
                style={{ width: `${job.progressPercent}%` }}
              />
            </div>
            {progressLabel && (
              <p className="editorial-batch-progress__current">{progressLabel}</p>
            )}
            {done && (
              <p className="gcr-alert gcr-alert--success editorial-batch-progress__done">
                {completionMessage(job)}
              </p>
            )}
            {job.errors.length > 0 && (
              <ul className="editorial-batch-progress__errors">
                {job.errors.map((err) => (
                  <li key={err.itemId}>
                    <strong>{err.title}</strong>: {err.message}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}

        {!job && jobQuery.isLoading && (
          <p className="gcr-card__description">Avvio job…</p>
        )}
      </div>
    </AppModal>
  );
}
