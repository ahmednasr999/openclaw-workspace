export function getRequestBaseUrl(request: Request): string {
  const url = new URL(request.url);
  const forwardedHost = request.headers.get("x-forwarded-host") || request.headers.get("host");
  const forwardedProto = request.headers.get("x-forwarded-proto") || url.protocol.replace(":", "");

  if (!forwardedHost) {
    return `${url.protocol}//${url.host}`;
  }

  return `${forwardedProto}://${forwardedHost}`;
}

export function toRedirectUrl(request: Request, path: string): URL {
  return new URL(path, getRequestBaseUrl(request));
}
