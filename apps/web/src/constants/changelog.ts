export type ChangelogReleaseType = "Alpha minor" | "Alpha patch" | "Alpha major";

export interface ChangelogRelease {
  version: string;
  date: string;
  type: ChangelogReleaseType;
  items: string[];
}

export const GCR_VERSION = "0.3.5-alpha";

export const CHANGELOG_RELEASES: ChangelogRelease[] = [
  {
    version: "0.3.5-alpha",
    date: "2026-06-13",
    type: "Alpha minor",
    items: [
      "Tab AI Context Preview: anteprima contesto passato ai moduli AI",
      "promptContext.previewText human-friendly; fullText invariato per moduli AI",
      "Avvisi fonti esterne (Trustpilot, Instagram) spostati in Brand Profile",
    ],
  },
  {
    version: "0.3.4-alpha",
    date: "2026-06-13",
    type: "Alpha minor",
    items: [
      "Product Knowledge: regole generali + schede prodotto Shopify",
      "Import file scoped solo per knowledge generale",
      "BrandContextBuilder espone productKnowledge machine-ready",
      "Product SEO usa knowledge generale + item specifico per prodotto",
    ],
  },
  {
    version: "0.3.3-alpha",
    date: "2026-06-13",
    type: "Alpha minor",
    items: [
      "Safe Claims & Red Flags: tab dedicata con import file e apply-proposal",
      "Migration 023 brand_safe_claims + contesto AI con fallback prudenza",
      "Product SEO: guardrail espliciti su claim vietati e red flags",
      "Overview con 5ª card Safe Claims; score su 4 moduli",
    ],
  },
  {
    version: "0.3.2-alpha",
    date: "2026-06-13",
    type: "Alpha minor",
    items: [
      "Import Brand Identity da singolo file (PDF, DOCX, TXT, MD)",
      "Proposta AI scoped + apply-proposal per Brand Identity",
      "BrandContextBuilder machine-ready con promptContext",
      "Form ufficiale aggiornato dopo apply proposta",
    ],
  },
  {
    version: "0.3.1-alpha",
    date: "2026-06-13",
    type: "Alpha minor",
    items: [
      "Brand Identity: posizionamento, valori, principi (salvataggio manuale)",
      "Visual Identity: logo, palette, font + estrazione da sito con apply-proposal",
      "Overview con 3 card di stato (Profile, Identity, Visual)",
      "BrandContextBuilder include i 3 moduli nel contesto AI",
      "Migration 022 brand_identities e brand_visual_identities",
    ],
  },
  {
    version: "0.3.0-alpha",
    date: "2026-06-13",
    type: "Alpha minor",
    items: [
      "Brand Intelligence semplificata: solo Overview + Brand Profile v1",
      "Enrich da fonti pubbliche con proposta AI revisionabile",
      "Apply-proposal: salvataggio esplicito profilo ufficiale",
      "BrandContextBuilder usa Brand Profile come contesto primario",
      "Rimossi da UI: wizard, import AI, brief, facts, section drafts",
      "Migration 021 brand_profile_v1",
    ],
  },
  {
    version: "0.2.7-alpha",
    date: "2026-06-13",
    type: "Alpha patch",
    items: [
      "Fix GET brief: campi nullable sourceFactIds/sourceDocumentIds normalizzati",
      "Mapper API brief read robusto contro NULL da JSONB",
      "Messaggio errore UI leggibile su apertura brief fallita",
    ],
  },
  {
    version: "0.2.6-alpha",
    date: "2026-06-13",
    type: "Alpha minor",
    items: [
      "Brand Intelligence Brief Mode — fonte primaria flessibile per moduli AI",
      "Synthesis brief senza validazione Pydantic bloccante per sezione",
      "Brief approvato usato da BrandContextBuilder (primarySource)",
      "UI Import: genera/revisiona/approva brief; facts e drafts secondari",
      "Migration 020 brand_intelligence_briefs",
    ],
  },
  {
    version: "0.2.5-alpha",
    date: "2026-06-13",
    type: "Alpha patch",
    items: [
      "Salvataggio fonti brand su batch esistente (PUT sources)",
      "Refresh context async: fetch + archivia bozze + rigenera",
      "UI Salva / Aggiorna e rigenera con polling e step 3 automatico",
      "Section drafts latestOnly: una bozza attiva per sezione",
      "Dati ufficiali e bozze applicate intatti",
    ],
  },
  {
    version: "0.2.4-alpha",
    date: "2026-06-13",
    type: "Alpha minor",
    items: [
      "Import AI: fonti brand esterne (sito, social, recensioni)",
      "Fetch pubblico leggero con warning se fonte non accessibile",
      "Sintesi sezione arricchita da file + fonti esterne",
      "Migration 019 brand_external_sources",
      "Nessun salvataggio automatico su BI ufficiale",
    ],
  },
  {
    version: "0.2.3-alpha",
    date: "2026-06-13",
    type: "Alpha minor",
    items: [
      "AI synthesis: bozze Brand Intelligence complete per sezione da documenti importati",
      "Review per sezione con editor strutturato, fonti e confidence",
      "Apply non distruttivo con rilevamento conflitti su dati ufficiali esistenti",
      "Migration 018 brand_section_drafts",
      "Facts estratti restano come livello di supporto/evidenza",
    ],
  },
  {
    version: "0.2.2-alpha",
    date: "2026-06-13",
    type: "Alpha patch",
    items: [
      "Import batch jobs: elaborazione async con progress tracking su DB",
      "Polling frontend ogni 2s durante estrazione AI",
      "Conflict detection per import incrementali (update_mode, previous_value)",
      "Storico import e review con badge conflitti",
      "Migration 017 brand_import_batches",
    ],
  },
  {
    version: "0.2.1-alpha",
    date: "2026-06-13",
    type: "Alpha patch",
    items: [
      "AI File Import v1: upload PDF/DOCX/TXT/MD con estrazione testo",
      "Extracted facts review: approve, modifica, sposta sezione, rifiuta, apply",
      "Onboarding dual-path in Overview: wizard manuale vs Import AI",
      "Migration 016 brand_source_documents + brand_extracted_facts",
      "Regola no auto-save: solo facts approvati nel contesto AI ufficiale",
    ],
  },
  {
    version: "0.2.0-alpha",
    date: "2026-06-13",
    type: "Alpha minor",
    items: [
      "Brand Intelligence Foundation: 10 modelli DB, migration 015, API CRUD",
      "Brand Knowledge Score e BrandIntelligenceContextBuilder per moduli AI",
      "UI Overview, wizard 7 step, tab per sezione, sidebar e shortcut",
      "Integrazione SEO non distruttiva (arricchimento prompt con fallback)",
      "Documentazione brand-intelligence e ai-architecture",
    ],
  },
  {
    version: "0.1.2-alpha",
    date: "2026-06-13",
    type: "Alpha patch",
    items: [
      "UX compatta Content SEO Optimizer",
      "KPI summary prodotti/categorie con score medio",
      "Rimozione tab Proposte dalla pagina principale",
      "Feedback sync/analyze dismissible (toast auto-dismiss)",
      "Miglioramenti visuali tabelle e header Product & Collection SEO",
    ],
  },
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
