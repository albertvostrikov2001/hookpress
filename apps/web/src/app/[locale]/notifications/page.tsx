"use client";

import { Button, Card, EmptyState, SkeletonCard } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type Notification,
} from "@/lib/api";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

export default function NotificationsPage() {
  const t = useTranslations("notifications");
  const tc = useTranslations("common");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<Notification[]>([]);
  const [filter, setFilter] = useState<"all" | "unread">("all");

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await listNotifications(filter === "unread");
      setItems(data.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : tc("error"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [filter]);

  return (
    <>
      <PageShell size="narrow">
        <PageHeader
          title={t("pageTitle")}
          subtitle={t("pageSubtitle")}
          actions={
            items.length > 0 ? (
              <Button variant="secondary" size="sm" onClick={() => void markAllNotificationsRead().then(load)}>
                {t("markAllRead")}
              </Button>
            ) : undefined
          }
        />

        <div className="mb-6 flex gap-2">
          <Button variant={filter === "all" ? "primary" : "ghost"} size="sm" onClick={() => setFilter("all")}>
            {t("filterAll")}
          </Button>
          <Button variant={filter === "unread" ? "primary" : "ghost"} size="sm" onClick={() => setFilter("unread")}>
            {t("filterUnread")}
          </Button>
        </div>

        {loading && (
          <div className="space-y-3">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {error && (
          <Card>
            <p className="text-sm text-[var(--hp-danger)]">{error}</p>
            <Button variant="secondary" className="mt-3" onClick={() => void load()}>
              {tc("retry")}
            </Button>
          </Card>
        )}

        {!loading && !error && items.length === 0 && (
          <EmptyState title={t("empty")} description={t("emptyHint")} />
        )}

        {!loading && !error && items.length > 0 && (
          <ul className="space-y-3">
            {items.map((n) => (
              <li key={n.id}>
                <Card className={n.read_at ? "opacity-70" : ""}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium">{n.title}</p>
                      {n.body && <p className="mt-1 text-sm text-[var(--hp-fg-muted)]">{n.body}</p>}
                      <p className="mt-2 font-mono text-xs text-[var(--hp-fg-muted)]">
                        {n.type} · {new Date(n.created_at).toLocaleString()}
                      </p>
                    </div>
                    {!n.read_at && (
                      <Button variant="ghost" size="sm" onClick={() => void markNotificationRead(n.id).then(load)}>
                        {t("markRead")}
                      </Button>
                    )}
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </PageShell>
      <Footer />
    </>
  );
}
