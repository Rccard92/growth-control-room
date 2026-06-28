import { describe, expect, it } from "vitest";
import { parseApiResponseBody } from "./api";

describe("parseApiResponseBody", () => {
  it("returns null for 204 No Content", async () => {
    const response = new Response(null, { status: 204 });
    await expect(parseApiResponseBody(response)).resolves.toBeNull();
  });

  it("returns null for 205 Reset Content", async () => {
    const response = new Response(null, { status: 205 });
    await expect(parseApiResponseBody(response)).resolves.toBeNull();
  });

  it("parses JSON body on 200", async () => {
    const response = new Response(JSON.stringify({ id: "abc" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
    await expect(parseApiResponseBody(response)).resolves.toEqual({ id: "abc" });
  });

  it("returns null for 200 with empty body", async () => {
    const response = new Response("", { status: 200 });
    await expect(parseApiResponseBody(response)).resolves.toBeNull();
  });

  it("parses JSON array when content-type is missing", async () => {
    const response = new Response("[1,2]", { status: 200 });
    await expect(parseApiResponseBody(response)).resolves.toEqual([1, 2]);
  });

  it("returns raw text for non-JSON body", async () => {
    const response = new Response("plain error", { status: 200 });
    await expect(parseApiResponseBody(response)).resolves.toBe("plain error");
  });
});
