import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { GrowthAuditPageFindingsPanel } from "./GrowthAuditPageFindingsPanel";

describe("GrowthAuditPageFindingsPanel", () => {
  it("shows Come risolvere section", () => {
    const html = renderToStaticMarkup(
      <GrowthAuditPageFindingsPanel
        findings={[
          {
            id: "f1",
            runId: "run",
            projectId: "proj",
            pageId: "page-1",
            category: "seo",
            severity: "critical",
            priority: "high",
            title: "Title troppo corto",
            description: "Il title ha meno di 30 caratteri.",
            recommendation: "Estendi il title con keyword e brand.",
            howToValidate: "Controlla il tag title nel sorgente.",
            status: "open",
          },
        ]}
      />,
    );

    expect(html).toContain("Come risolvere");
    expect(html).toContain("Estendi il title con keyword e brand.");
    expect(html).toContain("Critico");
  });

  it("shows empty state without findings", () => {
    const html = renderToStaticMarkup(<GrowthAuditPageFindingsPanel findings={[]} />);
    expect(html).toContain("Nessun problema tecnico prioritario rilevato per questa pagina.");
  });
});
