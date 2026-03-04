import { NextResponse } from "next/server";
import { AUTH_COOKIE } from "@/lib/auth";
import { toRedirectUrl } from "@/lib/request-url";

export async function POST(request: Request) {
  const response = NextResponse.redirect(toRedirectUrl(request, "/auth"));
  response.cookies.delete(AUTH_COOKIE);
  return response;
}
