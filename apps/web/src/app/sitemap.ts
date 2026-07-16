import type { MetadataRoute } from "next";
import { fetchArticles } from "@/lib/server-api";
import { routing } from "@/i18n/routing";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://hook.press";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPaths = ["", "/studio", "/office", "/market", "/feed", "/charts", "/chat", "/promo", "/login"];
  const entries: MetadataRoute.Sitemap = [];

  for (const locale of routing.locales) {
    for (const path of staticPaths) {
      entries.push({
        url: `${SITE_URL}/${locale}${path}`,
        lastModified: new Date(),
        changeFrequency: path === "" ? "weekly" : "daily",
        priority: path === "" ? 1 : 0.7,
      });
    }
  }

  try {
    const articles = await fetchArticles();
    for (const article of articles) {
      for (const locale of routing.locales) {
        entries.push({
          url: `${SITE_URL}/${locale}/feed/${article.slug}`,
          lastModified: article.published_at ? new Date(article.published_at) : new Date(),
          changeFrequency: "weekly",
          priority: 0.6,
        });
      }
    }
  } catch {
    // API may be offline during build
  }

  return entries;
}
