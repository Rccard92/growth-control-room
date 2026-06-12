export const CONTENT_SEO_ROW_LIMIT = 8;

export function sliceContentRows<T>(items: T[], expanded: boolean, limit = CONTENT_SEO_ROW_LIMIT): T[] {
  if (expanded) return items;
  return items.slice(0, limit);
}
