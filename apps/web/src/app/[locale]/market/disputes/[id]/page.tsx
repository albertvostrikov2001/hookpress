"use client";

import { useEffect, useState } from "react";
import { Badge, Button, Card, EmptyState, Input, SkeletonCard, useToast } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { Link } from "@/i18n/navigation";
import {
  addDisputeEvidence,
  getDispute,
  getToken,
  listDisputeEvidence,
  type Dispute,
  type DisputeEvidence,
} from "@/lib/api";
import { useTranslations } from "next-intl";
import { useParams, useRouter } from "next/navigation";

export default function DisputeDetailPage() {
  const t = useTranslations("market");
  const { toast } = useToast();
  const router = useRouter();
  const params = useParams();
  const disputeId = params.id as string;
  const [dispute, setDispute] = useState<Dispute | null>(null);
  const [evidence, setEvidence] = useState<DisputeEvidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [note, setNote] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    void (async () => {
      try {
        const [d, ev] = await Promise.all([getDispute(disputeId), listDisputeEvidence(disputeId)]);
        setDispute(d);
        setEvidence(ev);
      } catch (e) {
        toast(e instanceof Error ? e.message : t("error"), "error");
      } finally {
        setLoading(false);
      }
    })();
  }, [disputeId, router, t, toast]);

  async function submitEvidence() {
    if (!note.trim()) return;
    const item = await addDisputeEvidence(disputeId, note.trim());
    setEvidence((prev) => [...prev, item]);
    setNote("");
    toast(t("evidenceAdded"), "success");
  }

  return (
    <>
      <PageShell size="narrow">
        <PageHeader
          title={t("disputeDetail")}
          subtitle={dispute ? `#${dispute.id.slice(0, 8)}` : undefined}
          actions={
            dispute ? (
              <Link href={`/market/orders/${dispute.order_id}`} className="text-sm text-[var(--hp-accent)] hover:underline">
                {t("viewOrder")}
              </Link>
            ) : undefined
          }
        />

        {loading && <SkeletonCard />}
        {dispute && (
          <div className="space-y-6">
            <Card className="space-y-2 text-sm">
              <div className="flex flex-wrap gap-2">
                <Badge variant="accent">{dispute.status}</Badge>
              </div>
              <p>
                <span className="text-[var(--hp-fg-muted)]">{t("disputeReason")}:</span> {dispute.reason}
              </p>
              {dispute.resolution && (
                <p>
                  <span className="text-[var(--hp-fg-muted)]">{t("resolution")}:</span> {dispute.resolution}
                </p>
              )}
            </Card>

            <Card>
              <h2 className="mb-3 font-display font-semibold">{t("evidence")}</h2>
              {evidence.length === 0 ? (
                <EmptyState title={t("noEvidence")} description={t("noEvidenceHint")} />
              ) : (
                <ul className="mb-4 space-y-2 text-sm">
                  {evidence.map((e) => (
                    <li key={e.id} className="rounded border border-[var(--hp-border)] p-3">
                      <p className="font-mono text-[10px] text-[var(--hp-fg-muted)]">{e.uploaded_by.slice(0, 8)}</p>
                      <p className="mt-1 whitespace-pre-wrap">{e.body}</p>
                    </li>
                  ))}
                </ul>
              )}
              <div className="flex gap-2">
                <Input value={note} onChange={(e) => setNote(e.target.value)} placeholder={t("evidencePlaceholder")} className="flex-1" />
                <Button variant="primary" onClick={() => void submitEvidence()} disabled={!note.trim()}>
                  {t("addEvidence")}
                </Button>
              </div>
            </Card>
          </div>
        )}
      </PageShell>
      <Footer />
    </>
  );
}
