import type { BrandKnowledgeScore } from "@gcr/shared";

interface BrandScoreRingProps {
  score: BrandKnowledgeScore;
  size?: number;
}

const STATUS_LABELS: Record<BrandKnowledgeScore["status"], string> = {
  incomplete: "Incompleto",
  developing: "In sviluppo",
  ready: "Pronto",
};

export function BrandScoreRing({ score, size = 140 }: BrandScoreRingProps) {
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score.overallScore / 100) * circumference;

  return (
    <div className="bi-score-ring" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="url(#biScoreGradient)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
        <defs>
          <linearGradient id="biScoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#34d399" />
          </linearGradient>
        </defs>
      </svg>
      <div className="bi-score-ring__value">
        <span className="bi-score-ring__number">{score.overallScore}</span>
        <span className={`bi-score-ring__label bi-status--${score.status}`}>
          {STATUS_LABELS[score.status]}
        </span>
      </div>
    </div>
  );
}
