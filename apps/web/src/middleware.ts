import createIntlMiddleware from "next-intl/middleware";
import { type NextRequest, NextResponse } from "next/server";
import { routing } from "./i18n/routing";

const intlMiddleware = createIntlMiddleware(routing);

const TOKEN_COOKIE = "hookpress_access_token";

const PROTECTED_PREFIXES = [
  "/dashboard",
  "/studio",
  "/office",
  "/profile",
  "/notifications",
  "/settings",
  "/chat",
  "/market/account",
  "/market/orders",
  "/market/disputes",
  "/moderator",
  "/admin",
];

const ROLE_ROUTES: Record<string, string[]> = {
  "/moderator": ["moderator", "admin"],
  "/admin": ["admin", "moderator"],
};

function stripLocale(pathname: string): { locale: string; path: string } {
  const match = pathname.match(/^\/(en|ru)(\/|$)/);
  if (!match) return { locale: routing.defaultLocale, path: pathname };
  const locale = match[1];
  const rest = pathname.slice(locale.length + 1) || "/";
  return { locale, path: rest };
}

function decodeRoles(token: string): string[] {
  try {
    const payload = token.split(".")[1];
    if (!payload) return [];
    const json = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    return Array.isArray(json.roles) ? json.roles : [];
  } catch {
    return [];
  }
}

export function middleware(request: NextRequest) {
  const { locale, path } = stripLocale(request.nextUrl.pathname);
  const token = request.cookies.get(TOKEN_COOKIE)?.value;

  const isProtected = PROTECTED_PREFIXES.some(
    (prefix) => path === prefix || path.startsWith(`${prefix}/`),
  );

  if (isProtected && !token) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = `/${locale}/login`;
    loginUrl.searchParams.set("redirect", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (token) {
    const roles = decodeRoles(token);
    for (const [routePrefix, allowed] of Object.entries(ROLE_ROUTES)) {
      if (path === routePrefix || path.startsWith(`${routePrefix}/`)) {
        if (!allowed.some((role) => roles.includes(role))) {
          const homeUrl = request.nextUrl.clone();
          homeUrl.pathname = `/${locale}`;
          return NextResponse.redirect(homeUrl);
        }
      }
    }
  }

  return intlMiddleware(request);
}

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
