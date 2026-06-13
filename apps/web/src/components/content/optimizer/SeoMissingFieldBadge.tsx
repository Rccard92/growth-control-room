const FIELD_LABELS: Record<string, string> = {
  title: "Titolo",
  seoTitle: "SEO title",
  metaDescription: "Meta description",
  description: "Descrizione",
  handle: "Handle",
  imageAlt: "Alt immagini",
};

interface SeoMissingFieldBadgeProps {
  field: string;
  issues?: Record<string, unknown>[] | null;
}

export function SeoMissingFieldBadge({ field, issues }: SeoMissingFieldBadgeProps) {
  const match = (issues ?? []).find((issue) => {
    const issueField = String(issue.field ?? "");
    if (field === "seoTitle") return issueField === "seo_title";
    if (field === "metaDescription") return issueField === "seo_description";
    if (field === "imageAlt") return issueField === "media_images" || issueField === "image_alt";
    return issueField === field;
  });

  if (!match) return null;

  const severity = String(match.severity ?? "warning");
  return (
    <span className={`seo-missing-badge seo-missing-badge--${severity}`}>
      {String(match.message ?? "Campo da migliorare")}
    </span>
  );
}

export function breakdownFieldLabel(key: string): string {
  return FIELD_LABELS[key] ?? key;
}
