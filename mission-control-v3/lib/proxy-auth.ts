const PUBLIC_PATHS = ["/auth", "/api/auth/login"];

export interface ProxyDecision {
  allow: boolean;
  redirectTo?: string;
}

function isBypassedPath(pathname: string) {
  return (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.startsWith("/api/auth/logout")
  );
}

export function getProxyDecision(pathname: string, isAuthenticated: boolean): ProxyDecision {
  if (isBypassedPath(pathname)) {
    return { allow: true };
  }

  if (PUBLIC_PATHS.some((path) => pathname.startsWith(path))) {
    return { allow: true };
  }

  if (isAuthenticated) {
    return { allow: true };
  }

  return {
    allow: false,
    redirectTo: `/auth?next=${encodeURIComponent(pathname)}`,
  };
}
