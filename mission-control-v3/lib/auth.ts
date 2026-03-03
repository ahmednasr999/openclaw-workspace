import { cookies } from "next/headers";
import { hasValidAuthCookie } from "@/lib/auth-helpers";

export const AUTH_COOKIE = "mcv3_auth";

export async function isAuthenticated() {
  const store = await cookies();
  return hasValidAuthCookie(store.get(AUTH_COOKIE)?.value);
}
