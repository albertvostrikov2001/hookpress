"use client";

import { Badge, Button, Card, SkeletonCard } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import {
  getMe,
  listLoginEvents,
  listSessions,
  revokeAllSessions,
  revokeSession,
  type LoginEvent,
  type SessionInfo,
  type User,
} from "@/lib/api";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

export default function ProfilePage() {
  const t = useTranslations("profile");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loginEvents, setLoginEvents] = useState<LoginEvent[]>([]);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [me, sess, events] = await Promise.all([getMe(), listSessions(), listLoginEvents()]);
      setUser(me);
      setSessions(sess);
      setLoginEvents(events.slice(0, 10));
    } catch (e) {
      setError(e instanceof Error ? e.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <>
      <PageShell size="narrow">
        <PageHeader title={t("title")} subtitle={t("subtitle")} />

        {loading && (
          <div className="space-y-4">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {error && (
          <Card>
            <p className="text-sm text-[var(--hp-danger)]">{error}</p>
            <Button variant="secondary" className="mt-3" onClick={() => void load()}>
              {t("retry")}
            </Button>
          </Card>
        )}

        {user && !loading && (
          <div className="space-y-6">
            <Card>
              <h2 className="font-display text-lg font-semibold">{t("account")}</h2>
              <dl className="mt-4 space-y-3 text-sm">
                <div>
                  <dt className="text-[var(--hp-fg-muted)]">{t("displayName")}</dt>
                  <dd className="font-medium">{user.display_name}</dd>
                </div>
                <div>
                  <dt className="text-[var(--hp-fg-muted)]">{t("email")}</dt>
                  <dd className="font-mono">{user.email}</dd>
                </div>
                <div>
                  <dt className="text-[var(--hp-fg-muted)]">{t("roles")}</dt>
                  <dd className="mt-1 flex flex-wrap gap-2">
                    {user.roles.map((role) => (
                      <Badge key={role} variant="accent">
                        {role}
                      </Badge>
                    ))}
                  </dd>
                </div>
              </dl>
            </Card>

            <Card>
              <div className="mb-4 flex items-center justify-between gap-4">
                <h2 className="font-display text-lg font-semibold">{t("sessions")}</h2>
                <Button variant="secondary" size="sm" onClick={() => void revokeAllSessions().then(load)}>
                  {t("revokeAll")}
                </Button>
              </div>
              <ul className="space-y-3">
                {sessions.map((s) => (
                  <li key={s.id} className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] p-3 text-sm">
                    <p className="font-mono text-xs text-[var(--hp-fg-muted)]">{s.id.slice(0, 8)}…</p>
                    <p className="text-[var(--hp-fg-muted)]">{s.ip_address ?? t("unknownIp")}</p>
                    <p className="truncate text-xs">{s.user_agent ?? "—"}</p>
                    <Button variant="ghost" size="sm" className="mt-2" onClick={() => void revokeSession(s.id).then(load)}>
                      {t("revokeOne")}
                    </Button>
                  </li>
                ))}
              </ul>
            </Card>

            <Card>
              <h2 className="mb-4 font-display text-lg font-semibold">{t("loginHistory")}</h2>
              <ul className="space-y-2 text-sm">
                {loginEvents.map((ev) => (
                  <li key={ev.id} className="flex items-center justify-between gap-2 border-b border-[var(--hp-border)] pb-2">
                    <span className="font-mono text-xs">{new Date(ev.created_at).toLocaleString()}</span>
                    <Badge variant={ev.success ? "success" : "default"}>{ev.method}</Badge>
                  </li>
                ))}
                {loginEvents.length === 0 && <p className="text-[var(--hp-fg-muted)]">{t("noLoginEvents")}</p>}
              </ul>
            </Card>
          </div>
        )}
      </PageShell>
      <Footer />
    </>
  );
}
