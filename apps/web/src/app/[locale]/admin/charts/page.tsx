"use client";

import { useEffect, useState } from "react";
import { Button, Card, EmptyState, SkeletonCard, useToast } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { getChartSource, getMe, updateChartWeights, type ChartSource } from "@/lib/api";
import { useTranslations } from "next-intl";

const DEFAULT_SLUG = "demo-top-40";

export default function AdminChartsPage() {
  const t = useTranslations("admin");
  const { toast } = useToast();
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [source, setSource] = useState<ChartSource | null>(null);
  const [weightsJson, setWeightsJson] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void (async () => {
      try {
        const me = await getMe();
        const ok = me.roles.includes("admin");
        setAllowed(ok);
        if (ok) {
          const src = await getChartSource(DEFAULT_SLUG);
          setSource(src);
          setWeightsJson(JSON.stringify(src.source_weights, null, 2));
        }
      } catch {
        setAllowed(false);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function handleSave() {
    try {
      const weights = JSON.parse(weightsJson) as Record<string, number>;
      const sum = Object.values(weights).reduce((a, b) => a + b, 0);
      if (Math.abs(sum - 1) > 0.01) {
        toast(t("weightsMustSum"), "error");
        return;
      }
      const updated = await updateChartWeights(DEFAULT_SLUG, weights);
      setSource(updated);
      toast(t("weightsSaved"), "success");
    } catch {
      toast(t("weightsInvalid"), "error");
    }
  }

  if (allowed === null || loading) {
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
          <PageHeader title={t("chartsTitle")} />
          <Card>
            <p className="text-[var(--hp-danger)]">{t("chartsNoAccess")}</p>
          </Card>
        </PageShell>
        <Footer />
      </>
    );
  }

  return (
    <>
      <PageShell size="narrow">
        <PageHeader title={t("chartsTitle")} subtitle={t("chartsSubtitle")} badge="Admin" />

        {source ? (
          <Card className="space-y-4">
            <p className="text-sm text-[var(--hp-fg-muted)]">
              {source.name} · {source.slug}
            </p>
            <label className="block text-sm font-medium">{t("weightsJson")}</label>
            <textarea
              value={weightsJson}
              onChange={(e) => setWeightsJson(e.target.value)}
              rows={10}
              className="w-full rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] p-3 font-mono text-sm"
            />
            <Button variant="primary" onClick={() => void handleSave()}>
              {t("saveWeights")}
            </Button>
          </Card>
        ) : (
          <EmptyState title={t("noChartSource")} description={t("noChartSourceHint")} />
        )}
      </PageShell>
      <Footer />
    </>
  );
}
