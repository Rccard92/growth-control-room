import { describe, expect, it, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import type { GrowthAuditFinding, GrowthAuditPage } from "@gcr/shared";
import {
  GrowthAuditPageDrawer,
  handleDrawerEscapeKey,
} from "./GrowthAuditPageDrawer";

const samplePage: GrowthAuditPage = {
  id: "page-1",
  runId: "run-1",
  projectId: "proj-1",
  url: "https://solmielato.it/products/miele",
  normalizedUrl: "https://solmielato.it/products/miele",
  pageType: "product",
  source: "shopify_product",
  status: "analyzed",
  priority: "normal",
  title: "Miele di Limone",
  metaDescription: "Miele biologico siciliano dal gusto delicato.",
  canonicalUrl: "https://solmielato.it/products/miele",
  h1: "Miele di Limone",
  httpStatus: 200,
  score: 82,
  metadata: {
    technical: {
      schemaTypes: ["Product", "WebPage"],
      imagesTotal: 5,
      imagesMissingAlt: 1,
      linksInternal: 12,
      linksExternal: 2,
      robots: { noindex: false, nofollow: false },
    },
  },
};

const sampleFinding: GrowthAuditFinding = {
  id: "finding-1",
  runId: "run-1",
  projectId: "proj-1",
  pageId: "page-1",
  category: "seo",
  severity: "critical",
  priority: "high",
  title: "Title troppo corto",
  recommendation: "Estendi il title con keyword e brand.",
  status: "open",
};

const rescanProps = {
  projectId: "proj-1",
  runId: "run-1",
  runStatus: "completed",
  onRescan: vi.fn().mockResolvedValue(undefined),
};

describe("handleDrawerEscapeKey", () => {
  it("calls onClose when Escape is pressed", () => {
    const onClose = vi.fn();
    handleDrawerEscapeKey({ key: "Escape" } as KeyboardEvent, onClose);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("does not call onClose for other keys", () => {
    const onClose = vi.fn();
    handleDrawerEscapeKey({ key: "Enter" } as KeyboardEvent, onClose);
    expect(onClose).not.toHaveBeenCalled();
  });
});

describe("GrowthAuditPageDrawer", () => {
  it("renders role dialog and aria-modal", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain('role="dialog"');
    expect(html).toContain('aria-modal="true"');
  });

  it("renders URL, score, page type and Chiudi button", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("https://solmielato.it/products/miele");
    expect(html).toContain("82");
    expect(html).toContain("Buona");
    expect(html).toContain("Prodotto");
    expect(html).toContain("Chiudi");
    expect(html).toContain('aria-label="Chiudi"');
  });

  it("renders technical fields and enabled rescan button when run is completed", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        {...rescanProps}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Miele di Limone");
    expect(html).toContain("Miele biologico siciliano dal gusto delicato.");
    expect(html).toContain("Product, WebPage");
    expect(html).toContain("Riscansiona pagina");
    expect(html).not.toContain("in arrivo");
    expect(html).not.toContain("disabled");
    expect(html).toContain(
      "Usalo dopo aver corretto title, meta, immagini, schema o altri elementi tecnici.",
    );
  });

  it("shows Riprova scansione label for failed pages", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={{ ...samplePage, status: "failed", errorMessage: "Timeout" }}
        findings={[]}
        tasks={[]}
        {...rescanProps}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Riprova scansione");
    expect(html).toContain("Timeout");
  });

  it("disables rescan while run is active", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        {...rescanProps}
        runStatus="analyzing"
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("disabled");
  });

  it("shows loading label when isRescanning", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        {...rescanProps}
        isRescanning
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Riscansione in corso…");
    expect(html).toContain("disabled");
  });

  it("renders Come risolvere when findings have recommendation", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[sampleFinding]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Come risolvere");
    expect(html).toContain("Estendi il title con keyword e brand.");
  });

  it("renders empty states when no findings or tasks", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open
        page={samplePage}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toContain("Nessun problema tecnico prioritario rilevato per questa pagina.");
    expect(html).toContain("Nessun task tecnico aperto per questa pagina.");
  });

  it("returns null when closed", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageDrawer
        open={false}
        page={samplePage}
        findings={[]}
        tasks={[]}
        onClose={() => undefined}
      />,
    );

    expect(html).toBe("");
  });
});
