const createNextIntlPlugin = require("next-intl/plugin");

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const internalApi = (
  process.env.INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000"
).replace(/\/$/, "");

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? internalApi;
const wsUrl =
  process.env.NEXT_PUBLIC_WS_URL ??
  internalApi.replace(/^http:\/\//, "ws://").replace(/^https:\/\//, "wss://");

function cspConnectSrc() {
  const origins = new Set(["'self'", apiUrl, wsUrl, internalApi]);
  try {
    for (const base of [apiUrl, internalApi, wsUrl]) {
      const parsed = new URL(base.startsWith("ws") ? base.replace(/^ws/, "http") : base);
      origins.add(parsed.origin);
      origins.add(parsed.origin.replace(/^http/, "ws").replace(/^https/, "wss"));
    }
  } catch {
    // keep defaults
  }
  origins.add("http://localhost:8000");
  origins.add("http://127.0.0.1:8000");
  origins.add("ws://localhost:8000");
  origins.add("ws://127.0.0.1:8000");
  // Allow Render API host for WebSocket (HTTP uses same-origin proxy).
  origins.add("https:");
  origins.add("wss:");
  return Array.from(origins).join(" ");
}

/** @type {import('next').NextConfig} */
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Content-Security-Policy",
    value: `default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src ${cspConnectSrc()}; frame-ancestors 'none'`,
  },
  {
    key: "Strict-Transport-Security",
    value: "max-age=31536000; includeSubDomains",
  },
];

const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  transpilePackages: ["@hookpress/ui"],
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${internalApi}/api/v1/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },
};

module.exports = withNextIntl(nextConfig);
