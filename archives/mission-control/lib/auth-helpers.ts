export const AUTH_COOKIE_VALUE = "ok";

export function hasValidAuthCookie(value?: string) {
  return value === AUTH_COOKIE_VALUE;
}

export function isValidAccessToken(token: string, expectedToken?: string) {
  return Boolean(expectedToken) && token === expectedToken;
}
