import type { EditorialArticlePayload } from "@gcr/shared";

export interface EditorialQualityAnalysis {
  skillPackUsed: string;
  skillPackVersion: string;
  strongCount: number;
  listCount: number;
  boxCount: number;
  hasCta: boolean;
  hasLongParagraphs: boolean;
  warnings: string[];
}

const STRONG_RE = /<strong\b[^>]*>/gi;
const LIST_RE = /<(?:ul|ol)\b[^>]*>/gi;
const BOX_RE = /<div\s+class="(gcr-article-note|gcr-product-tip|gcr-article-cta)"/gi;
const P_RE = /<p\b[^>]*>([\s\S]*?)<\/p>/gi;
const STRIP_HTML = /<[^>]+>/g;

function countWords(text: string): number {
  const plain = text.replace(STRIP_HTML, " ").replace(/\s+/g, " ").trim();
  if (!plain) return 0;
  return plain.split(" ").length;
}

export function analyzeEditorialQuality(
  article: EditorialArticlePayload,
): EditorialQualityAnalysis {
  const html = article.bodyHtml ?? "";
  const strongCount = (html.match(STRONG_RE) ?? []).length;
  const listCount = (html.match(LIST_RE) ?? []).length;
  const boxCount = (html.match(BOX_RE) ?? []).length;

  let hasLongParagraphs = false;
  for (const match of html.matchAll(P_RE)) {
    if (countWords(match[1] ?? "") > 80) {
      hasLongParagraphs = true;
      break;
    }
  }

  const hasCta = Boolean(article.cta?.trim() || article.communityCta?.trim());

  return {
    skillPackUsed: article.skillPackUsed?.trim() || "—",
    skillPackVersion: article.skillPackVersion?.trim() || "—",
    strongCount,
    listCount,
    boxCount,
    hasCta,
    hasLongParagraphs,
    warnings: article.warnings ?? [],
  };
}
