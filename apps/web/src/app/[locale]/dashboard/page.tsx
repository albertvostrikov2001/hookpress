"use client";

import { Badge, Card, EmptyState, ProgressRail, SkeletonCard } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { Link, useRouter } from "@/i18n/navigation";
import {
  getWalletBalance,
  listNotifications,
  listOfficeProjects,
  listStudioProjects,
  type Notification,
  type OfficeProjectSummary,
  type StudioProjectSummary,
} from "@/lib/api";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

function taskProgress(status: string) {
  switch (status) {
    case "PENDING":
      return 15;
    case "PROCESSING":
      return 55;
    case "SUCCEEDED":
      return 100;
    case "FAILED":
      return 100;
    default:
      return 0;
  }
}

function taskVariant(status: string): "default" | "success" | "warning" | "danger" {
  if (status === "SUCCEEDED") return "success";
  if (status === "FAILED") return "danger";
  if (status === "PROCESSING") return "warning";
  return "default";
}

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [studio, setStudio] = useState<StudioProjectSummary[]>([]);
  const [office, setOffice] = useState<OfficeProjectSummary[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [walletMinor, setWalletMinor] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [studioRes, officeRes, notifRes, walletRes] = await Promise.all([
        listStudioProjects(),
        listOfficeProjects(),
        listNotifications(),
        getWalletBalance().catch(() => null),
      ]);
      setStudio(studioRes.items.slice(0, 5));
      setOffice(officeRes.items.slice(0, 5));
      setNotifications(notifRes.items.slice(0, 5));
      setWalletMinor(walletRes?.balance_minor ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("error"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const activeTasks = studio.flatMap((p) =>
    (p.ai_tasks ?? [])
      .filter((task) => !["SUCCEEDED", "CANCELLED"].includes(task.status))
      .map((task) => ({ ...task, projectTitle: p.title })),
  );

  const isEmpty = !loading && !error && studio.length === 0 && office.length === 0;

  return (
    <>
      <PageShell>
        <PageHeader title={t("title")} subtitle={t("subtitle")} />

        {loading && (
          <div className="grid gap-4 md:grid-cols-2">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {error && (
          <Card className="border-[var(--hp-danger)]/30 bg-[var(--hp-danger)]/5">
            <p className="text-sm text-[var(--hp-danger)]">{error}</p>
            <button type="button" className="mt-3 text-sm text-[var(--hp-accent)] underline" onClick={() => void load()}>
              {t("retry")}
            </button>
          </Card>
        )}

        {isEmpty && (
          <EmptyState
            title={t("emptyTitle")}
            description={t("emptyDescription")}
            actionLabel={t("emptyCta")}
            onAction={() => router.push("/studio")}
          />
        )}

        {!loading && !error && !isEmpty && (
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-display text-lg font-semibold">{t("studioProjects")}</h2>
                <Link href="/studio" className="text-sm text-[var(--hp-accent)] hover:underline">
                  {t("viewAll")}
                </Link>
              </div>
              {studio.length === 0 ? (
                <p className="text-sm text-[var(--hp-fg-muted)]">{t("noStudio")}</p>
              ) : (
                <ul className="space-y-3">
                  {studio.map((p) => (
                    <li key={p.id} className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] p-3">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-medium">{p.title}</p>
                          <p className="font-mono text-xs text-[var(--hp-fg-muted)]">
                            {p.genre ?? "—"} · {p.status}
                          </p>
                        </div>
                        <Badge variant="accent">{p.status}</Badge>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-display text-lg font-semibold">{t("aiTasks")}</h2>
              </div>
              {activeTasks.length === 0 ? (
                <p className="text-sm text-[var(--hp-fg-muted)]">{t("noTasks")}</p>
              ) : (
                <ul className="space-y-4">
                  {activeTasks.slice(0, 4).map((task) => (
                    <li key={task.id}>
                      <p className="mb-1 text-sm font-medium">{task.projectTitle}</p>
                      <p className="mb-2 font-mono text-xs text-[var(--hp-fg-muted)]">
                        {task.task_type} · {task.status}
                      </p>
                      <ProgressRail
                        value={taskProgress(task.status)}
                        label={task.status}
                        variant={taskVariant(task.status)}
                        size="sm"
                      />
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-display text-lg font-semibold">{t("officeReleases")}</h2>
                <Link href="/office" className="text-sm text-[var(--hp-accent)] hover:underline">
                  {t("viewAll")}
                </Link>
              </div>
              {office.length === 0 ? (
                <p className="text-sm text-[var(--hp-fg-muted)]">{t("noOffice")}</p>
              ) : (
                <ul className="space-y-3">
                  {office.map((p) => (
                    <li key={p.id} className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] p-3">
                      <p className="font-medium">{p.title}</p>
                      <p className="font-mono text-xs text-[var(--hp-fg-muted)]">{p.status}</p>
                      {p.releases[0] && (
                        <p className="mt-1 text-xs text-[var(--hp-fg-muted)]">
                          {p.releases[0].title} · {p.releases[0].status}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </Card>

            <Card>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-display text-lg font-semibold">{t("notifications")}</h2>
                <Link href="/notifications" className="text-sm text-[var(--hp-accent)] hover:underline">
                  {t("viewAll")}
                </Link>
              </div>
              {notifications.length === 0 ? (
                <p className="text-sm text-[var(--hp-fg-muted)]">{t("noNotifications")}</p>
              ) : (
                <ul className="space-y-2">
                  {notifications.map((n) => (
                    <li key={n.id} className="text-sm">
                      <p className="font-medium">{n.title}</p>
                      {n.body && <p className="text-[var(--hp-fg-muted)]">{n.body}</p>}
                    </li>
                  ))}
                </ul>
              )}
              {walletMinor !== null && (
                <div className="mt-6 border-t border-[var(--hp-border)] pt-4">
                  <p className="text-xs text-[var(--hp-fg-muted)]">{t("wallet")}</p>
                  <p className="font-display text-2xl font-semibold tabular-nums">
                    {(walletMinor / 100).toFixed(2)} ₽
                  </p>
                </div>
              )}
            </Card>
          </div>
        )}
      </PageShell>
      <Footer />
    </>
  );
}
