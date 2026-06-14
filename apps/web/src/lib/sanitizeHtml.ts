const ALLOWED_TAGS = new Set([
  "h2",
  "h3",
  "p",
  "ul",
  "ol",
  "li",
  "strong",
  "em",
  "a",
  "blockquote",
]);

const ALLOWED_LINK_ATTRS = new Set(["href", "title", "rel"]);

function isSafeHref(href: string): boolean {
  const lower = href.trim().toLowerCase();
  if (lower.startsWith("javascript:") || lower.startsWith("data:") || lower.startsWith("vbscript:")) {
    return false;
  }
  return true;
}

function sanitizeElement(el: Element): string {
  const tag = el.tagName.toLowerCase();
  if (!ALLOWED_TAGS.has(tag)) {
    return Array.from(el.childNodes).map((child) => sanitizeNode(child)).join("");
  }

  if (tag === "a") {
    const attrs: string[] = [];
    for (const attr of Array.from(el.attributes)) {
      if (!ALLOWED_LINK_ATTRS.has(attr.name.toLowerCase())) continue;
      if (attr.name.toLowerCase() === "href" && !isSafeHref(attr.value)) continue;
      attrs.push(`${attr.name}="${attr.value.replace(/"/g, "&quot;")}"`);
    }
    const attrStr = attrs.length ? ` ${attrs.join(" ")}` : "";
    const inner = Array.from(el.childNodes).map((child) => sanitizeNode(child)).join("");
    return `<${tag}${attrStr}>${inner}</${tag}>`;
  }

  const inner = Array.from(el.childNodes).map((child) => sanitizeNode(child)).join("");
  return `<${tag}>${inner}</${tag}>`;
}

function sanitizeNode(node: Node): string {
  if (node.nodeType === Node.TEXT_NODE) {
    return node.textContent ?? "";
  }
  if (node.nodeType === Node.ELEMENT_NODE) {
    return sanitizeElement(node as Element);
  }
  return "";
}

export function sanitizeArticleHtml(html: string): string {
  if (!html.trim()) return "";
  const doc = new DOMParser().parseFromString(html, "text/html");
  return Array.from(doc.body.childNodes).map((child) => sanitizeNode(child)).join("");
}
