interface BrandImportProgressBarProps {
  percent: number;
  currentStep?: string | null;
  processedFiles?: number;
  totalFiles?: number;
  totalFacts?: number;
}

export function BrandImportProgressBar({
  percent,
  currentStep,
  processedFiles,
  totalFiles,
  totalFacts,
}: BrandImportProgressBarProps) {
  const safePercent = Math.max(0, Math.min(100, percent));

  return (
    <div className="bi-progress">
      <div className="bi-progress__header">
        <span className="bi-progress__label">{currentStep ?? "Elaborazione in corso…"}</span>
        <span className="bi-progress__percent">{safePercent}%</span>
      </div>
      <div className="bi-progress__track" role="progressbar" aria-valuenow={safePercent} aria-valuemin={0} aria-valuemax={100}>
        <div className="bi-progress__fill" style={{ width: `${safePercent}%` }} />
      </div>
      <div className="bi-progress__meta">
        {totalFiles != null && totalFiles > 0 && (
          <span>
            File {processedFiles ?? 0}/{totalFiles}
          </span>
        )}
        {totalFacts != null && totalFacts > 0 && <span>{totalFacts} informazioni estratte</span>}
      </div>
    </div>
  );
}
