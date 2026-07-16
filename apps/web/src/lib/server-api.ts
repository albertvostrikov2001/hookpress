const API_URL =
  process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type FeedArticle = {
  id: string;
  title: string;
  slug: string;
  summary: string | null;
  body: string;
  seo_title: string | null;
  seo_description: string | null;
  published_at: string | null;
  view_count?: number;
};

export async function serverFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    next: { revalidate: 60 },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${path}`);
  }
  return res.json();
}

export async function fetchArticles(): Promise<FeedArticle[]> {
  const data = await serverFetch<FeedArticleList>("/api/v1/feed/articles");
  return data.items;
}

type FeedArticleList = { items: FeedArticle[]; total: number; has_more: boolean };

export async function fetchArticleBySlug(slug: string): Promise<FeedArticle | null> {
  const articles = await fetchArticles();
  return articles.find((a) => a.slug === slug) ?? null;
}

export async function fetchChart(slug = "demo-top-40") {
  return serverFetch<{
    source: { name: string; slug: string; is_mock: boolean; source_weights?: Record<string, number> };
    week_date: string;
    entries: {
      position: number;
      title: string;
      artist: string;
      previous_position?: number | null;
      position_change?: number | null;
    }[];
  }>(`/api/v1/charts/${slug}`);
}
