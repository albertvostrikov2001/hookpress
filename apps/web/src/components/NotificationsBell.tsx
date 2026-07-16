"use client";

import { Button, Modal } from "@hookpress/ui";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type Notification,
} from "@/lib/api";

export function NotificationsBell({ onUnreadChange }: { onUnreadChange?: (count: number) => void }) {
  const t = useTranslations("notifications");
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notification[]>([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await listNotifications();
      setItems(data.items);
      setUnread(data.unread_count);
      onUnreadChange?.(data.unread_count);
    } catch {
      setItems([]);
      setUnread(0);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    const id = window.setInterval(() => void load(), 60_000);
    return () => window.clearInterval(id);
  }, []);

  async function handleOpen() {
    setOpen(true);
    await load();
  }

  async function handleRead(id: string) {
    await markNotificationRead(id);
    await load();
  }

  async function handleReadAll() {
    await markAllNotificationsRead();
    await load();
  }

  return (
    <>
      <button
        type="button"
        onClick={() => void handleOpen()}
        className="relative rounded-md border border-[var(--hp-border)] px-2 py-1 text-sm text-[var(--hp-fg-muted)] hover:text-[var(--hp-fg)]"
        aria-label={t("title")}
      >
        🔔
        {unread > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--hp-accent)] px-1 text-[10px] text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      <Modal open={open} onClose={() => setOpen(false)} title={t("title")}>
        {loading && <p className="text-sm text-[var(--hp-fg-muted)]">…</p>}
        {!loading && items.length === 0 && (
          <p className="text-sm text-[var(--hp-fg-muted)]">{t("empty")}</p>
        )}
        <ul className="max-h-80 space-y-2 overflow-y-auto">
          {items.map((n) => (
            <li
              key={n.id}
              className={`rounded-md border border-[var(--hp-border)] p-3 text-sm ${n.read_at ? "opacity-60" : ""}`}
            >
              <p className="font-medium">{n.title}</p>
              {n.body && <p className="text-[var(--hp-fg-muted)]">{n.body}</p>}
              {!n.read_at && (
                <button
                  type="button"
                  className="mt-2 text-xs text-[var(--hp-accent)]"
                  onClick={() => void handleRead(n.id)}
                >
                  ✓
                </button>
              )}
            </li>
          ))}
        </ul>
        {items.length > 0 && (
          <div className="mt-4">
            <Button variant="secondary" type="button" onClick={() => void handleReadAll()}>
              {t("markAllRead")}
            </Button>
          </div>
        )}
      </Modal>
    </>
  );
}
