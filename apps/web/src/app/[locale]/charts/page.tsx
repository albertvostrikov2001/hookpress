"use client";

import { useEffect, useState } from "react";
import { Card, SkeletonCard } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { fetchChartClient, type ChartPayload } from "@/lib/charts";
import { useTranslations } from "next-intl";

function formatDelta(change: number | null | undefined, t: (key: string) => string): string {
  if (change == null) return t("newEntry");
  if (change > 0) return `▲ ${change}`;
  if (change < 0) return `▼ ${Math.abs(change)}`;
  return "—";
}

export default function ChartsPage() {
  const t = useTranslations("charts");
  const [chart, setChart] = useState<ChartPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void fetchChartClient("demo-top-40")
      .then(setChart)
      .catch((e) => setError(e instanceof Error ? e.message : t("unavailable")))
      .finally(() => setLoading(false));
  }, [t]);

  return (
    <div className="flex min-h-[calc(100vh-64px)] flex-col">
      <PageShell size="narrow">
        <PageHeader
          title={t("title")}
          subtitle={t("subtitle")}
          badge={t("mockWarning")}
          badgeVariant="warning"
        />

        {loading && (
          <div className="space-y-3">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {!loading && chart && (
          <Card padding="none" className="overflow-hidden">
            <div className="border-b border-[var(--hp-border)] px-6 py-4">
              <p className="text-sm text-[var(--hp-fg-muted)]">
                {t("week")}: {chart.week_date} · {chart.source.name}
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--hp-border)] bg-[var(--hp-bg-subtle)] text-left text-[var(--hp-fg-muted)]">
                    <th className="px-6 py-3 font-medium">#</th>
                    <th className="px-6 py-3 font-medium">{t("track")}</th>
                    <th className="px-6 py-3 font-medium">{t("artist")}</th>
                    <th className="px-6 py-3 font-medium">{t("delta")}</th>
                  </tr>
                </thead>
                <tbody>
                  {chart.entries.map((e) => (
                    <tr
                      key={e.position}
                      className="border-b border-[var(--hp-border)] transition hover:bg-[var(--hp-bg-subtle)]"
                    >
                      <td className="px-6 py-3 font-mono text-[var(--hp-accent)]">{e.position}</td>
                      <td className="px-6 py-3 font-medium">{e.title}</td>
                      <td className="px-6 py-3 text-[var(--hp-fg-muted)]">{e.artist}</td>
                      <td
                        className={`px-6 py-3 font-mono text-xs ${
                          (e.position_change ?? 0) > 0
                            ? "text-[var(--hp-success)]"
                            : (e.position_change ?? 0) < 0
                              ? "text-[var(--hp-danger)]"
                              : "text-[var(--hp-fg-muted)]"
                        }`}
                      >
                        {formatDelta(e.position_change, t)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {!loading && !chart && (
          <Card padding="lg" className="text-center">
            <p className="text-[var(--hp-fg-muted)]">{error ?? t("unavailable")}</p>
            <button
              type="button"
              className="mt-4 text-sm font-medium text-[var(--hp-accent)] hover:underline"
              onClick={() => {
                setLoading(true);
                setError(null);
                void fetchChartClient("demo-top-40")
                  .then(setChart)
                  .catch((e) => setError(e instanceof Error ? e.message : t("unavailable")))
                  .finally(() => setLoading(false));
              }}
            >
              {t("retry")}
            </button>
          </Card>
        )}
      </PageShell>
      <Footer />
    </div>
  );
}
