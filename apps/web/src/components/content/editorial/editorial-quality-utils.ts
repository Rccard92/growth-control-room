import type { EditorialArticlePayload, EditorialSafeClaimFlag } from "@gcr/shared";

export interface EditorialQualityAnalysis {
  skillPackUsed: string;
  skillPackVersion: string;
  strongCount: number;
  strongInRange: boolean;
  listCount: number;
  boxCount: number;
  hasCta: boolean;
  hasCtaBox: boolean;
  hasBodyWrapper: boolean;
  hasLongParagraphs: boolean;
  hasSeoTitle: boolean;
  hasMetaDescription: boolean;
  seoTitleLength: number;
  metaDescriptionLength: number;
  seoTitleInRange: boolean;
  metaDescriptionInRange: boolean;
  safeClaimFlags: EditorialSafeClaimFlag[];
  warnings: string[];
}

const SEO_TITLE_MAX = 60;
const META_DESCRIPTION_MAX = 160;

const STRONG_RE = /<strong\b[^>]*>/gi;
const LIST_RE = /<(?:ul|ol)\b[^>]*>/gi;
const BOX_RE = /<div\s+class="(gcr-article-note|gcr-product-tip|gcr-article-cta)"/gi;
const BODY_WRAPPER_RE = /<div\s+class="gcr-article-body"/i;
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
  const hasBodyWrapper = BODY_WRAPPER_RE.test(html);
  const hasCtaBox = /class="gcr-article-cta"/i.test(html);

  let hasLongParagraphs = false;
  for (const match of html.matchAll(P_RE)) {
    if (countWords(match[1] ?? "") > 80) {
      hasLongParagraphs = true;
      break;
    }
  }

  const hasCta = Boolean(article.cta?.trim() || article.communityCta?.trim());
  const seoTitle = article.seoTitle?.trim() ?? "";
  const metaDescription = article.metaDescription?.trim() ?? "";

  return {
    skillPackUsed: article.skillPackUsed?.trim() || "—",
    skillPackVersion: article.skillPackVersion?.trim() || "—",
    strongCount,
    strongInRange: strongCount >= 6 && strongCount <= 9,
    listCount,
    boxCount,
    hasCta,
    hasCtaBox,
    hasBodyWrapper,
    hasLongParagraphs,
    hasSeoTitle: Boolean(seoTitle),
    hasMetaDescription: Boolean(metaDescription),
    seoTitleLength: seoTitle.length,
    metaDescriptionLength: metaDescription.length,
    seoTitleInRange: seoTitle.length > 0 && seoTitle.length <= SEO_TITLE_MAX,
    metaDescriptionInRange:
      metaDescription.length > 0 && metaDescription.length <= META_DESCRIPTION_MAX,
    safeClaimFlags: article.safeClaimFlags ?? [],
    warnings: article.warnings ?? [],
  };
}
