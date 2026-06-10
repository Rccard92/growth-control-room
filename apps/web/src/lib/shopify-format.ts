export function formatShopifyMoney(value: string, currency?: string | null): string {
  const amount = Number(value);
  if (Number.isNaN(amount)) return value;
  return new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: currency ?? "EUR",
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatShopifyDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("it-IT", { dateStyle: "short" }).format(date);
}

export function formatShopifyDateTime(value?: string | null): string {
  if (!value) return "Mai sincronizzato";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Data non disponibile";
  return new Intl.DateTimeFormat("it-IT", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatDurationSeconds(seconds?: number): string {
  if (seconds == null || Number.isNaN(seconds)) return "—";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}
