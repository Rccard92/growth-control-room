import { Link } from "react-router-dom";

interface CommandCardProps {
  icon: string;
  label: string;
  description: string;
  to: string;
}

export function CommandCard({ icon, label, description, to }: CommandCardProps) {
  return (
    <Link to={to} className="gcr-command-card">
      <span className="gcr-command-card__icon">{icon}</span>
      <span className="gcr-command-card__label">{label}</span>
      <span className="gcr-command-card__desc">{description}</span>
    </Link>
  );
}
