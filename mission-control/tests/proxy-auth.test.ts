import { describe, expect, it } from "vitest";
import { getProxyDecision } from "../lib/proxy-auth";

describe("proxy auth redirect behavior", () => {
  it("allows public auth paths", () => {
    expect(getProxyDecision("/auth", false).allow).toBe(true);
    expect(getProxyDecision("/api/auth/login", false).allow).toBe(true);
  });

  it("redirects protected paths when unauthenticated", () => {
    const decision = getProxyDecision("/dashboard", false);
    expect(decision.allow).toBe(false);
    expect(decision.redirectTo).toBe("/auth?next=%2Fdashboard");
  });

  it("allows protected paths when authenticated", () => {
    const decision = getProxyDecision("/dashboard", true);
    expect(decision.allow).toBe(true);
    expect(decision.redirectTo).toBeUndefined();
  });
});
