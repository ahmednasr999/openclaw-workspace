import { describe, expect, it } from "vitest";
import { toRedirectUrl } from "../lib/request-url";

describe("request redirect host preservation", () => {
  it("uses forwarded host and proto when present", () => {
    const request = new Request("http://localhost:3200/api/auth/login", {
      headers: {
        "x-forwarded-host": "srv1352768.tail945bbc.ts.net",
        "x-forwarded-proto": "https",
      },
    });

    const redirectUrl = toRedirectUrl(request, "/dashboard");
    expect(redirectUrl.toString()).toBe("https://srv1352768.tail945bbc.ts.net/dashboard");
  });

  it("falls back to request url host", () => {
    const request = new Request("http://localhost:3200/api/auth/logout");
    const redirectUrl = toRedirectUrl(request, "/auth");

    expect(redirectUrl.toString()).toBe("http://localhost:3200/auth");
  });
});
