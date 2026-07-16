/** Server-side API base (Render: INTERNAL_API_URL at runtime). */
export function resolveServerApiBase(): string {
  return (
    process.env.INTERNAL_API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000"
  ).replace(/\/$/, "");
}

/** Browser uses same-origin /api/v1 (Next.js rewrite → backend). */
export function resolveClientApiBase(): string {
  if (typeof window === "undefined") return resolveServerApiBase();
  return "";
}

export function httpToWs(httpBase: string): string {
  return httpBase.replace(/^https:\/\//, "wss://").replace(/^http:\/\//, "ws://");
}

declare global {
  interface Window {
    __HOOKPRESS_API_BASE__?: string;
  }
}

/** WebSocket base — direct to API (cannot proxy WS through Next rewrites). */
export function resolveWsBase(): string {
  const explicit = process.env.NEXT_PUBLIC_WS_URL;
  if (explicit) return explicit.replace(/\/$/, "");

  if (typeof window !== "undefined" && window.__HOOKPRESS_API_BASE__) {
    return httpToWs(window.__HOOKPRESS_API_BASE__);
  }

  return httpToWs(resolveServerApiBase());
}
