export type ChangelogReleaseType = "Alpha minor" | "Alpha patch" | "Alpha major";

export interface ChangelogRelease {
  version: string;
  date: string;
  type: ChangelogReleaseType;
  items: string[];
}

export const GCR_VERSION = "0.1.1-alpha";

export const CHANGELOG_RELEASES: ChangelogRelease[] = [
  {
    version: "0.1.1-alpha",
    date: "2026-06-13",
    type: "Alpha patch",
    items: [
      "Product & Collection SEO Optimizer: modal di modifica più leggibile (portal, 720px, footer sticky)",
      "Campi Shopify precompilati con currentValues camelCase",
      "Badge stato campo: OK / Mancante / Da migliorare",
      "Flusso AI: preview proposta, copia nel form, nessuna applicazione automatica",
      "SEO skill pack interno ispirato da claude-seo (MIT)",
      "Changelog piattaforma e policy di versioning Alpha",
    ],
  },
  {
    version: "0.1.0-alpha",
    date: "2026-06-01",
    type: "Alpha minor",
    items: [
      "Shopify OAuth connection",
      "Shopify Sync v2",
      "Shopify Control Room / E-commerce dashboard",
      "Content SEO foundation",
      "Product & Collection SEO Optimizer (score, analisi, proposte, approve/apply)",
    ],
  },
];
