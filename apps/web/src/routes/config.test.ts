import { describe, expect, it } from "vitest";
import { APP_ROUTES, PROJECT_NAV } from "./config";

describe("routes config", () => {
  it("exports projectGrowthAudit route", () => {
    expect(APP_ROUTES.projectGrowthAudit("proj-1")).toBe("/projects/proj-1/audit");
  });

  it("includes Growth Audit in PROJECT_NAV", () => {
    const auditNav = PROJECT_NAV.find((item) => item.label === "Growth Audit");
    expect(auditNav).toBeDefined();
    expect(auditNav?.to).toBe("audit");
    expect(auditNav?.icon).toBe("↗");
  });
});
