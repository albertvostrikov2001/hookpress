"use client";

import { useEffect, useState } from "react";
import { Button, Card, EmptyState, Input, SkeletonCard, useToast } from "@hookpress/ui";
import { Link } from "@/i18n/navigation";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { getMe, getMarketOrder, getDispute, listNotifications, resolveDispute, reviewDispute, type Dispute, type MarketOrder } from "@/lib/api";
import { useTranslations } from "next-intl";

export default function ModeratorPage() {
  const t = useTranslations("moderator");
  const { toast } = useToast();
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [disputeId, setDisputeId] = useState("");
  const [dispute, setDispute] = useState<Dispute | null>(null);
  const [order, setOrder] = useState<MarketOrder | null>(null);
  const [queueIds, setQueueIds] = useState<string[]>([]);

  useEffect(() => {
    void (async () => {
      try {
        const me = await getMe();
        const ok = me.roles.some((r) => r === "moderator" || r === "admin");
        setAllowed(ok);
        if (ok) {
          const notes = await listNotifications();
          const ids = notes.items
            .map((n) => {
              const data = n.data as { dispute_id?: string } | null;
              return data?.dispute_id;
            })
            .filter((id): id is string => Boolean(id));
          setQueueIds([...new Set(ids)]);
        }
      } catch {
        setAllowed(false);
      }
    })();
  }, []);

  async function loadDispute(id: string) {
    const d = await getDispute(id);
    setDispute(d);
    setDisputeId(id);
    try {
      setOrder(await getMarketOrder(d.order_id));
    } catch {
      setOrder(null);
    }
  }

  async function handleReview() {
    if (!dispute) return;
    const updated = await reviewDispute(dispute.id);
    setDispute(updated);
    toast(t("reviewStarted"), "info");
  }

  async function handleResolve(refund: boolean) {
    if (!dispute) return;
    await resolveDispute(
      dispute.id,
      refund ? "Full refund to buyer" : "Release funds to seller",
      refund ? order?.amount_minor : 0,
    );
    await loadDispute(dispute.id);
    toast(t("resolved"), "success");
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
          <PageHeader title={t("title")} />
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
        <PageHeader title={t("title")} subtitle={t("subtitle")} badge="Moderator" />

        {queueIds.length > 0 && (
          <Card className="mb-6">
            <h2 className="mb-3 font-display font-semibold">{t("queue")}</h2>
            <ul className="flex flex-wrap gap-2">
              {queueIds.map((id) => (
                <li key={id}>
                  <Button variant="secondary" size="sm" onClick={() => void loadDispute(id)}>
                    {id.slice(0, 8)}…
                  </Button>
                </li>
              ))}
            </ul>
          </Card>
        )}

        <Card className="mb-6">
          <div className="flex gap-2">
            <Input
              value={disputeId}
              onChange={(e) => setDisputeId(e.target.value)}
              placeholder={t("disputeId")}
              className="flex-1"
            />
            <Button variant="primary" onClick={() => disputeId && void loadDispute(disputeId)}>
              {t("load")}
            </Button>
          </div>
        </Card>

        {dispute ? (
          <Card className="space-y-3">
            <p>
              <span className="text-[var(--hp-fg-muted)]">{t("status")}:</span> {dispute.status}
            </p>
            <p>
              <span className="text-[var(--hp-fg-muted)]">{t("orderId")}:</span>{" "}
              <Link href={`/market/orders/${dispute.order_id}`} className="text-[var(--hp-accent)] hover:underline">
                {dispute.order_id.slice(0, 8)}…
              </Link>
            </p>
            <p>
              <span className="text-[var(--hp-fg-muted)]">{t("reason")}:</span> {dispute.reason}
            </p>
            <Link href={`/market/disputes/${dispute.id}`}>
              <Button variant="secondary" size="sm">
                {t("viewDisputeDetail")}
              </Button>
            </Link>
            <div className="flex flex-wrap gap-2 pt-2">
              {dispute.status === "OPEN" && (
                <Button variant="secondary" onClick={() => void handleReview()}>
                  {t("review")}
                </Button>
              )}
              {["OPEN", "UNDER_REVIEW"].includes(dispute.status) && (
                <>
                  <Button variant="primary" onClick={() => void handleResolve(false)}>
                    {t("resolveSeller")}
                  </Button>
                  <Button variant="secondary" onClick={() => void handleResolve(true)}>
                    {t("resolveRefund")}
                  </Button>
                </>
              )}
            </div>
          </Card>
        ) : (
          <EmptyState title={t("empty")} description={t("emptyHint")} />
        )}
      </PageShell>
      <Footer />
    </>
  );
}
