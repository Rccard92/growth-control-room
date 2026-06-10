interface MetricCardProps {
  label: string;
  value: string | number;
  meta?: string;
}

export function MetricCard({ label, value, meta }: MetricCardProps) {
  return (
    <div className="gcr-card">
      <p className="gcr-card__label">{label}</p>
      <p className="gcr-card__value">{value}</p>
      {meta && <p className="gcr-card__meta">{meta}</p>}
    </div>
  );
}
