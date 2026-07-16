const createNextIntlPlugin = require("next-intl/plugin");

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const wsUrl =
  process.env.NEXT_PUBLIC_WS_URL ??
  apiUrl.replace(/^http:\/\//, "ws://").replace(/^https:\/\//, "wss://");

function cspConnectSrc() {
  const origins = new Set(["'self'", apiUrl, wsUrl]);
  try {
    const parsed = new URL(apiUrl);
    origins.add(parsed.origin);
    origins.add(parsed.origin.replace(/^http/, "ws").replace(/^https/, "wss"));
  } catch {
    // keep defaults
  }
  origins.add("http://localhost:8000");
  origins.add("http://127.0.0.1:8000");
  origins.add("ws://localhost:8000");
  origins.add("ws://127.0.0.1:8000");
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
