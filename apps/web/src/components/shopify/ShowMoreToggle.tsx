interface ShowMoreToggleProps {
  total: number;
  limit: number;
  expanded: boolean;
  onToggle: () => void;
}

export function ShowMoreToggle({ total, limit, expanded, onToggle }: ShowMoreToggleProps) {
  if (total <= limit) return null;

  return (
    <button type="button" className="shopify-show-more" onClick={onToggle}>
      {expanded ? "Mostra meno" : `Mostra tutto (${total})`}
    </button>
  );
}
