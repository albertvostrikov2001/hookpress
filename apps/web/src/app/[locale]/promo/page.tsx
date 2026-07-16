"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, EmptyState, SkeletonCard, useToast } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { Link } from "@/i18n/navigation";
import {
  createCampaign,
  getToken,
  listCampaigns,
  type Campaign,
} from "@/lib/api";
import { useTranslations } from "next-intl";

export default function PromoPage() {
  const t = useTranslations("promo");
  const tc = useTranslations("common");
  const { toast } = useToast();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [name, setName] = useState("");
  const [loggedIn, setLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listCampaigns();
      setCampaigns(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : tc("error"));
    } finally {
      setLoading(false);
    }
  }, [tc]);

  useEffect(() => {
    setLoggedIn(!!getToken());
  }, []);

  useEffect(() => {
    if (loggedIn) void load();
    else setLoading(false);
  }, [loggedIn, load]);

  async function create() {
    if (!name.trim()) return;
    setCreating(true);
    try {
      await createCampaign(name.trim());
      setName("");
      toast(t("campaignCreated"), "success");
      await load();
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-64px)] flex-col">
      <PageShell>
        <PageHeader title={t("title")} subtitle={t("subtitle")} badge="Promo" />

        {!loggedIn && (
          <Card padding="lg" className="text-center">
            <p className="text-sm text-[var(--hp-fg-muted)]">{t("loginRequired")}</p>
            <Link href="/login" className="mt-4 inline-block text-sm text-[var(--hp-accent)] hover:underline">
              {t("signIn")}
            </Link>
          </Card>
        )}

        {loggedIn && (
          <>
            <Card padding="lg" className="mb-8">
              <p className="mb-4 text-sm text-[var(--hp-fg-muted)]">{t("createHint")}</p>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
                <div className="flex-1">
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={t("namePlaceholder")}
                    className="w-full rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] px-3 py-2 text-sm"
                    onKeyDown={(e) => e.key === "Enter" && void create()}
                  />
                </div>
                <Button variant="primary" onClick={() => void create()} disabled={!name.trim() || creating}>
                  {t("create")}
                </Button>
              </div>
            </Card>

            {loading && (
              <div className="grid gap-4 sm:grid-cols-2">
                <SkeletonCard />
                <SkeletonCard />
              </div>
            )}

            {error && (
              <Card className="mb-6 border-[var(--hp-danger)]/30">
                <p className="text-sm text-[var(--hp-danger)]">{error}</p>
                <Button variant="secondary" className="mt-3" size="sm" onClick={() => void load()}>
                  {tc("retry")}
                </Button>
              </Card>
            )}

            {!loading && !error && campaigns.length === 0 && (
              <EmptyState title={t("emptyTitle")} description={t("emptyHint")} />
            )}

            <ul className="grid gap-4 sm:grid-cols-2">
              {campaigns.map((c) => (
                <li key={c.id}>
                  <Card padding="lg" hover>
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-display font-semibold">{c.name}</h3>
                      <Badge variant="accent">{c.status}</Badge>
                    </div>
                    <p className="mt-2 font-mono text-sm tabular-nums text-[var(--hp-fg-muted)]">
                      {t("budget")}: {(c.budget_minor / 100).toFixed(2)} ₽
                    </p>
                  </Card>
                </li>
              ))}
            </ul>
          </>
        )}
      </PageShell>
      <Footer />
    </div>
  );
}
