interface BrandOfficialVsDraftDiffProps {
  official?: unknown;
  draft?: unknown;
  fieldLabel: string;
}

function formatVal(v: unknown): string {
  if (v == null || v === "") return "—";
  if (Array.isArray(v)) return v.join(", ");
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

export function BrandOfficialVsDraftDiff({ official, draft, fieldLabel }: BrandOfficialVsDraftDiffProps) {
  const off = formatVal(official);
  const dr = formatVal(draft);
  if (off === dr || off === "—") return null;

  return (
    <div className="bi-draft-diff">
      <span className="bi-draft-diff__label">{fieldLabel}</span>
      <div className="bi-draft-diff__row">
        <span className="bi-draft-diff__col">
          <em>Esistente</em>
          {off}
        </span>
        <span className="bi-draft-diff__col bi-draft-diff__col--new">
          <em>Nuova bozza</em>
          {dr}
        </span>
      </div>
    </div>
  );
}
