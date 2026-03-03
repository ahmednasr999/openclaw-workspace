import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { hasValidAuthCookie } from "@/lib/auth-helpers";
import { getProxyDecision } from "@/lib/proxy-auth";
import { toRedirectUrl } from "@/lib/request-url";

export function proxy(request: NextRequest) {
  if (process.env.MCV3_PUBLIC === "1") {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;
  const token = request.cookies.get("mcv3_auth")?.value;
  const decision = getProxyDecision(pathname, hasValidAuthCookie(token));

  if (decision.allow) {
    return NextResponse.next();
  }

  const loginUrl = toRedirectUrl(request, decision.redirectTo || "/auth");
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|.*\\.png$).*)"],
};
