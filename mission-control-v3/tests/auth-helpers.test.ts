import { describe, expect, it } from "vitest";
import { hasValidAuthCookie, isValidAccessToken } from "../lib/auth-helpers";

describe("auth helpers", () => {
  it("validates auth cookie value", () => {
    expect(hasValidAuthCookie("ok")).toBe(true);
    expect(hasValidAuthCookie("bad")).toBe(false);
    expect(hasValidAuthCookie(undefined)).toBe(false);
  });

  it("validates access token against expected token", () => {
    expect(isValidAccessToken("secret", "secret")).toBe(true);
    expect(isValidAccessToken("secret", "other")).toBe(false);
    expect(isValidAccessToken("secret", undefined)).toBe(false);
  });
});
