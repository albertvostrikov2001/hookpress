"use client";

import { useEffect, useState } from "react";
import { Button, Card, Input, SkeletonCard } from "@hookpress/ui";
import { addFeedComment, getToken, listFeedComments, type FeedComment } from "@/lib/api";
import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";

type FeedCommentsProps = {
  articleId: string;
};

export function FeedComments({ articleId }: FeedCommentsProps) {
  const t = useTranslations("feed");
  const [comments, setComments] = useState<FeedComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [text, setText] = useState("");
  const [loggedIn, setLoggedIn] = useState(false);

  async function load() {
    setLoading(true);
    try {
      setComments(await listFeedComments(articleId));
    } catch {
      setComments([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLoggedIn(!!getToken());
    void load();
  }, [articleId]);

  async function submit() {
    if (!text.trim()) return;
    await addFeedComment(articleId, text.trim());
    setText("");
    await load();
  }

  return (
    <Card className="mt-8">
      <h2 className="mb-4 font-display text-lg font-semibold">{t("comments")}</h2>

      {loading && <SkeletonCard />}

      {!loading && comments.length === 0 && (
        <p className="mb-4 text-sm text-[var(--hp-fg-muted)]">{t("noComments")}</p>
      )}

      <ul className="mb-6 space-y-3">
        {comments.map((c) => (
          <li key={c.id} className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] p-3 text-sm">
            <div className="mb-1 flex items-center gap-2">
              <Link
                href={`/market/profiles/user/${c.user_id}`}
                className="font-mono text-xs text-[var(--hp-accent)] hover:underline"
              >
                {c.user_id.slice(0, 8)}
              </Link>
              <time className="font-mono text-[10px] text-[var(--hp-fg-muted)]">
                {new Date(c.created_at).toLocaleString()}
              </time>
            </div>
            <p className="whitespace-pre-wrap">{c.body}</p>
          </li>
        ))}
      </ul>

      {loggedIn ? (
        <div className="flex gap-2">
          <Input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={t("commentPlaceholder")}
            className="flex-1"
            onKeyDown={(e) => e.key === "Enter" && void submit()}
          />
          <Button variant="primary" onClick={() => void submit()} disabled={!text.trim()}>
            {t("postComment")}
          </Button>
        </div>
      ) : (
        <p className="text-sm text-[var(--hp-fg-muted)]">
          <Link href="/login" className="text-[var(--hp-accent)] hover:underline">
            {t("loginToComment")}
          </Link>
        </p>
      )}
    </Card>
  );
}
