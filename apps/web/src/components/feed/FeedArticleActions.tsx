"use client";

import { useState } from "react";
import { Button } from "@hookpress/ui";
import { bookmarkFeedArticle, likeFeedArticle, recordFeedView } from "@/lib/api";
import { useTranslations } from "next-intl";

type FeedArticleActionsProps = {
  articleId: string;
  initialViews?: number;
};

export function FeedArticleActions({ articleId, initialViews = 0 }: FeedArticleActionsProps) {
  const t = useTranslations("feed");
  const [views, setViews] = useState(initialViews);
  const [liked, setLiked] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [recorded, setRecorded] = useState(false);

  async function handleView() {
    if (recorded) return;
    const res = await recordFeedView(articleId);
    setViews(res.view_count);
    setRecorded(true);
  }

  async function handleLike() {
    await likeFeedArticle(articleId);
    setLiked(true);
  }

  async function handleBookmark() {
    await bookmarkFeedArticle(articleId);
    setBookmarked(true);
  }

  return (
    <div className="flex flex-wrap items-center gap-3 border-t border-[var(--hp-border)] pt-6">
      <Button variant="ghost" size="sm" onClick={() => void handleView()}>
        {t("views")}: {views}
      </Button>
      <Button variant={liked ? "primary" : "secondary"} size="sm" onClick={() => void handleLike()}>
        {t("like")}
      </Button>
      <Button variant={bookmarked ? "primary" : "secondary"} size="sm" onClick={() => void handleBookmark()}>
        {t("bookmark")}
      </Button>
    </div>
  );
}
