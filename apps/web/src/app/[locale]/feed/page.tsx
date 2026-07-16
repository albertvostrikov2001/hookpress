"use client";

import { useCallback, useEffect, useState } from "react";
import { Button, Card, SkeletonCard } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { Link } from "@/i18n/navigation";
import { listFeedArticles, listFeedCategories, listFeedTags, type FeedArticle, type FeedCategory, type FeedTag } from "@/lib/api";
import { useTranslations } from "next-intl";

const PAGE_SIZE = 12;

export default function FeedPage() {
  const t = useTranslations("feed");
  const [articles, setArticles] = useState<FeedArticle[]>([]);
  const [categories, setCategories] = useState<FeedCategory[]>([]);
  const [tags, setTags] = useState<FeedTag[]>([]);
  const [category, setCategory] = useState("");
  const [tag, setTag] = useState("");
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (nextOffset: number, append: boolean) => {
      setLoading(true);
      setError(null);
      try {
        const data = await listFeedArticles({
          category: category || undefined,
          tag: tag || undefined,
          limit: PAGE_SIZE,
          offset: nextOffset,
        });
        setArticles(append ? (prev) => [...prev, ...data.items] : data.items);
        setTotal(data.total);
        setHasMore(data.has_more);
        setOffset(nextOffset);
      } catch (e) {
        if (!append) {
          setArticles([]);
          setError(e instanceof Error ? e.message : t("error"));
        }
      } finally {
        setLoading(false);
      }
    },
    [category, tag, t],
  );

  useEffect(() => {
    void Promise.all([listFeedCategories(), listFeedTags()])
      .then(([cats, tagList]) => {
        setCategories(cats);
        setTags(tagList);
      })
      .catch(() => {
        setCategories([]);
        setTags([]);
      });
  }, []);

  useEffect(() => {
    void load(0, false);
  }, [load]);

  return (
    <div className="flex min-h-[calc(100vh-64px)] flex-col">
      <PageShell>
        <PageHeader title={t("title")} subtitle={t("subtitle")} badge="Feed" />

        {categories.length > 0 && (
          <Card padding="sm" className="mb-6">
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setCategory("")}
                className={`rounded-[var(--hp-radius)] px-3 py-1.5 text-sm ${
                  !category ? "bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]" : "text-[var(--hp-fg-muted)] hover:bg-[var(--hp-bg-subtle)]"
                }`}
              >
                {t("allCategories")}
              </button>
              {categories.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setCategory(c.slug)}
                  className={`rounded-[var(--hp-radius)] px-3 py-1.5 text-sm ${
                    category === c.slug
                      ? "bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]"
                      : "text-[var(--hp-fg-muted)] hover:bg-[var(--hp-bg-subtle)]"
                  }`}
                >
                  {c.name}
                </button>
              ))}
            </div>
            <p className="mt-2 font-mono text-xs text-[var(--hp-fg-muted)]">
              {t("articleCount", { count: total })}
            </p>
          </Card>
        )}

        {tags.length > 0 && (
          <Card padding="sm" className="mb-6">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--hp-fg-muted)]">{t("tags")}</p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setTag("")}
                className={`rounded-full px-3 py-1 text-xs ${
                  !tag ? "bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]" : "border border-[var(--hp-border)] text-[var(--hp-fg-muted)]"
                }`}
              >
                {t("allTags")}
              </button>
              {tags.map((tg) => (
                <button
                  key={tg.id}
                  type="button"
                  onClick={() => setTag(tg.slug)}
                  className={`rounded-full px-3 py-1 text-xs ${
                    tag === tg.slug
                      ? "bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]"
                      : "border border-[var(--hp-border)] text-[var(--hp-fg-muted)] hover:border-[var(--hp-accent)]/40"
                  }`}
                >
                  {tg.name}
                </button>
              ))}
            </div>
          </Card>
        )}

        {loading && articles.length === 0 && (
          <div className="grid gap-4 md:grid-cols-2">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        <ul className="grid gap-4 md:grid-cols-2">
          {articles.map((a) => (
            <li key={a.id}>
              <Card hover padding="lg" className="h-full">
                <Link href={`/feed/${a.slug}`} className="block">
                  <h2 className="text-lg font-semibold transition hover:text-[var(--hp-accent)]">{a.title}</h2>
                  {a.summary && (
                    <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-[var(--hp-fg-muted)]">{a.summary}</p>
                  )}
                  {a.tags && a.tags.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {a.tags.slice(0, 3).map((tg) => (
                        <span key={tg.id} className="rounded-full border border-[var(--hp-border)] px-2 py-0.5 text-[10px] text-[var(--hp-fg-muted)]">
                          {tg.name}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="mt-4 flex items-center justify-between text-sm">
                    <span className="font-medium text-[var(--hp-accent)]">{t("readMore")} →</span>
                    {a.view_count != null && (
                      <span className="font-mono text-xs text-[var(--hp-fg-muted)]">
                        {t("views")}: {a.view_count}
                      </span>
                    )}
                  </div>
                </Link>
              </Card>
            </li>
          ))}
        </ul>

        {!loading && error && (
          <Card padding="lg" className="mb-6 text-center">
            <p className="text-[var(--hp-danger)]">{error}</p>
            <Button variant="secondary" className="mt-4" onClick={() => void load(0, false)}>
              {t("retry")}
            </Button>
          </Card>
        )}

        {!loading && !error && articles.length === 0 && (
          <Card padding="lg" className="text-center">
            <p className="font-medium">{t("empty")}</p>
            <p className="mt-2 text-sm text-[var(--hp-fg-muted)]">{t("emptyHint")}</p>
          </Card>
        )}

        {hasMore && (
          <Button variant="secondary" className="mt-6" disabled={loading} onClick={() => void load(offset + PAGE_SIZE, true)}>
            {t("loadMore")}
          </Button>
        )}
      </PageShell>
      <Footer />
    </div>
  );
}
