interface ShopifyKpiCardProps {
  label: string;
  value: string | number;
  meta?: string;
  accent?: "violet" | "cyan" | "amber" | "rose" | "emerald" | "default";
}

export function ShopifyKpiCard({
  label,
  value,
  meta,
  accent = "default",
}: ShopifyKpiCardProps) {
  return (
    <div className={`shopify-kpi shopify-kpi--${accent}`}>
      <p className="shopify-kpi__label">{label}</p>
      <p className="shopify-kpi__value">{value}</p>
      {meta && <p className="shopify-kpi__meta">{meta}</p>}
    </div>
  );
}
