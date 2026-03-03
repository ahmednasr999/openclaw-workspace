import { NextResponse } from "next/server";
import { AUTH_COOKIE } from "@/lib/auth";
import { isValidAccessToken } from "@/lib/auth-helpers";
import { toRedirectUrl } from "@/lib/request-url";

export async function POST(request: Request) {
  const formData = await request.formData();
  const token = String(formData.get("token") || "");
  const nextPath = String(formData.get("next") || "/dashboard");

  const expectedToken = process.env.MISSION_CONTROL_TOKEN;

  if (!isValidAccessToken(token, expectedToken)) {
    return NextResponse.redirect(toRedirectUrl(request, "/auth"));
  }

  const response = NextResponse.redirect(toRedirectUrl(request, nextPath));
  response.cookies.set(AUTH_COOKIE, "ok", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
  });

  return response;
}
