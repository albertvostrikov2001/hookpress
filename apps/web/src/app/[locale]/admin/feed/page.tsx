"use client";

import { useEffect, useState } from "react";
import { Button, Card, EmptyState, Input, SkeletonCard, Textarea, useToast } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import {
  approveFeedArticle,
  createFeedArticle,
  getMe,
  ingestRssFeed,
  rejectFeedArticle,
  type FeedArticle,
} from "@/lib/api";
import { useTranslations } from "next-intl";

export default function AdminFeedPage() {
  const t = useTranslations("admin");
  const { toast } = useToast();
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [articleId, setArticleId] = useState("");
  const [drafts, setDrafts] = useState<FeedArticle[]>([]);
  const [rssUrl, setRssUrl] = useState("");
  const [ingesting, setIngesting] = useState(false);

  useEffect(() => {
    void getMe()
      .then((me) => setAllowed(me.roles.some((r) => r === "admin" || r === "moderator")))
      .catch(() => setAllowed(false));
  }, []);

  async function handleCreate() {
    const article = await createFeedArticle(title, body);
    setDrafts((prev) => [article, ...prev]);
    setTitle("");
    setBody("");
    setArticleId(article.id);
    toast(t("draftCreated"), "success");
  }

  async function handleApprove() {
    if (!articleId) return;
    const article = await approveFeedArticle(articleId);
    setDrafts((prev) => prev.map((a) => (a.id === article.id ? article : a)));
    toast(t("approved"), "success");
  }

  async function handleReject() {
    if (!articleId) return;
    const article = await rejectFeedArticle(articleId);
    setDrafts((prev) => prev.map((a) => (a.id === article.id ? article : a)));
    toast(t("rejected"), "info");
  }

  async function handleIngestRss() {
    if (!rssUrl.trim()) return;
    setIngesting(true);
    try {
      const result = await ingestRssFeed(rssUrl.trim());
      toast(t("rssIngested", { count: result.ingested }), "success");
      setRssUrl("");
    } catch (e) {
      toast(e instanceof Error ? e.message : t("rssError"), "error");
    } finally {
      setIngesting(false);
    }
  }

  if (allowed === null) {
    return (
      <PageShell size="narrow">
        <SkeletonCard />
      </PageShell>
    );
  }

  if (!allowed) {
    return (
      <>
        <PageShell size="narrow">
          <PageHeader title={t("feedTitle")} />
          <Card>
            <p className="text-[var(--hp-danger)]">{t("noAccess")}</p>
          </Card>
        </PageShell>
        <Footer />
      </>
    );
  }

  return (
    <>
      <PageShell size="narrow">
        <PageHeader title={t("feedTitle")} subtitle={t("feedSubtitle")} badge="Admin" />

        <Card className="mb-6 space-y-3">
          <h2 className="font-display font-semibold">{t("createArticle")}</h2>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder={t("articleTitle")} />
          <Textarea value={body} onChange={(e) => setBody(e.target.value)} rows={6} label={t("articleBody")} />
          <Button variant="primary" onClick={() => void handleCreate()} disabled={!title || !body}>
            {t("submit")}
          </Button>
        </Card>

        <Card className="mb-6 space-y-3">
          <h2 className="font-display font-semibold">{t("rssIngest")}</h2>
          <p className="text-sm text-[var(--hp-fg-muted)]">{t("rssIngestHint")}</p>
          <Input value={rssUrl} onChange={(e) => setRssUrl(e.target.value)} placeholder={t("rssUrlPlaceholder")} />
          <Button variant="secondary" onClick={() => void handleIngestRss()} disabled={!rssUrl.trim() || ingesting}>
            {t("rssIngestButton")}
          </Button>
        </Card>

        <Card className="mb-6 space-y-3">
          <h2 className="font-display font-semibold">{t("moderation")}</h2>
          <Input value={articleId} onChange={(e) => setArticleId(e.target.value)} placeholder={t("articleId")} />
          <div className="flex gap-2">
            <Button variant="primary" onClick={() => void handleApprove()}>
              {t("approve")}
            </Button>
            <Button variant="secondary" onClick={() => void handleReject()}>
              {t("reject")}
            </Button>
          </div>
        </Card>

        {drafts.length > 0 ? (
          <ul className="space-y-2">
            {drafts.map((a) => (
              <li key={a.id}>
                <Card padding="sm">
                  <button type="button" className="w-full text-left" onClick={() => setArticleId(a.id)}>
                    <span className="font-medium">{a.title}</span>
                    <span className="ml-2 font-mono text-xs text-[var(--hp-fg-muted)]">
                      {a.moderation_status} · {a.status}
                    </span>
                  </button>
                </Card>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title={t("noDrafts")} description={t("noDraftsHint")} />
        )}
      </PageShell>
      <Footer />
    </>
  );
}
