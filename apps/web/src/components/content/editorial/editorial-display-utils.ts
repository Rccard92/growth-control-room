import type { ContentSeoEditorialItem } from "@gcr/shared";

export function getEditorialDisplayTitle(item: ContentSeoEditorialItem): string {
  const articleTitle = String(item.articlePayload?.title ?? "").trim();
  if (articleTitle) return articleTitle;

  const briefPayload = item.briefPayload as { proposedTitle?: string } | null | undefined;
  const briefTitle = String(briefPayload?.proposedTitle ?? "").trim();
  if (briefTitle) return briefTitle;

  const planned = String(item.title ?? "").trim();
  if (planned) return planned;

  return "Contenuto editoriale";
}
