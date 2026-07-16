import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import { FeedArticleActions } from "@/components/feed/FeedArticleActions";
import { FeedComments } from "@/components/feed/FeedComments";
import { Footer } from "@/components/layout/Footer";
import { PageShell } from "@/components/layout/PageShell";
import { Link } from "@/i18n/navigation";
import { fetchArticleBySlug } from "@/lib/server-api";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://hook.press";

type Props = { params: Promise<{ locale: string; slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug, locale } = await params;
  const article = await fetchArticleBySlug(slug);
  if (!article) return { title: "Article not found" };

  const title = article.seo_title ?? article.title;
  const description = article.seo_description ?? article.summary ?? undefined;
  const url = `${SITE_URL}/${locale}/feed/${slug}`;

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      url,
      type: "article",
      publishedTime: article.published_at ?? undefined,
    },
    twitter: { card: "summary_large_image", title, description },
  };
}

export default async function FeedArticlePage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("feed");
  const tc = await getTranslations("common");

  const article = await fetchArticleBySlug(slug);
  if (!article) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.summary ?? article.seo_description,
    datePublished: article.published_at,
    url: `${SITE_URL}/${locale}/feed/${slug}`,
    author: { "@type": "Organization", name: "hook.press" },
  };

  return (
    <>
      <PageShell size="narrow">
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
        <Link href="/feed" className="mb-6 inline-flex text-sm text-[var(--hp-accent)] hover:underline">
          ← {tc("back")} {t("title")}
        </Link>
        <article>
          <header className="mb-8 space-y-3">
            <h1 className="font-display text-3xl font-bold tracking-tight md:text-4xl">{article.title}</h1>
            {article.summary && <p className="text-lg text-[var(--hp-fg-muted)]">{article.summary}</p>}
            {article.published_at && (
              <time className="font-mono text-xs text-[var(--hp-fg-muted)]">
                {new Date(article.published_at).toLocaleDateString(locale)}
              </time>
            )}
          </header>
          <div className="prose prose-invert max-w-none whitespace-pre-wrap leading-relaxed text-[var(--hp-fg)]">
            {article.body}
          </div>
          <FeedArticleActions articleId={article.id} initialViews={article.view_count ?? 0} />
          <FeedComments articleId={article.id} />
        </article>
      </PageShell>
      <Footer />
    </>
  );
}
