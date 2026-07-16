"use client";

import { useEffect, useState } from "react";
import { Badge, Button, Card, Input, Modal, SkeletonCard, StatusStepper, Textarea, useToast } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { Link } from "@/i18n/navigation";
import {
  createOrderSpecVersion,
  getDisputeByOrder,
  getMarketOrder,
  getMe,
  getOrderDeliverables,
  getOrderMessages,
  getOrderSpecVersions,
  openDispute,
  sendOrderMessage,
  type MarketOrder,
  type OrderDeliverable,
  type OrderMessage,
  type OrderSpecVersion,
} from "@/lib/api";
import { useTranslations } from "next-intl";
import { useParams } from "next/navigation";

const ORDER_STEPS = ["CREATED", "AWAITING_PAYMENT", "FUNDS_HELD", "IN_PROGRESS", "DELIVERED", "COMPLETED"];

export default function MarketOrderPage() {
  const t = useTranslations("market");
  const { toast } = useToast();
  const params = useParams();
  const orderId = params.id as string;
  const [order, setOrder] = useState<MarketOrder | null>(null);
  const [messages, setMessages] = useState<OrderMessage[]>([]);
  const [specs, setSpecs] = useState<OrderSpecVersion[]>([]);
  const [deliverables, setDeliverables] = useState<OrderDeliverable[]>([]);
  const [myId, setMyId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [messageText, setMessageText] = useState("");
  const [specText, setSpecText] = useState("");
  const [disputeReason, setDisputeReason] = useState("");
  const [disputeId, setDisputeId] = useState<string | null>(null);
  const [showDispute, setShowDispute] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [o, m, s, d, me] = await Promise.all([
        getMarketOrder(orderId),
        getOrderMessages(orderId),
        getOrderSpecVersions(orderId),
        getOrderDeliverables(orderId),
        getMe(),
      ]);
      setOrder(o);
      setMessages(m);
      setSpecs(s);
      setDeliverables(d);
      setMyId(me.id);
      try {
        const dispute = await getDisputeByOrder(orderId);
        setDisputeId(dispute.id);
      } catch {
        setDisputeId(null);
      }
    } catch (e) {
      toast(e instanceof Error ? e.message : t("error"), "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [orderId]);

  async function postMessage() {
    if (!messageText.trim()) return;
    await sendOrderMessage(orderId, messageText);
    setMessageText("");
    setMessages(await getOrderMessages(orderId));
  }

  async function postSpec() {
    if (!specText.trim()) return;
    await createOrderSpecVersion(orderId, specText);
    setSpecText("");
    setSpecs(await getOrderSpecVersions(orderId));
    toast(t("specSaved"), "success");
  }

  async function handleDispute() {
    if (!disputeReason.trim()) return;
    const dispute = await openDispute(orderId, disputeReason);
    setDisputeId(dispute.id);
    setShowDispute(false);
    await load();
    toast(t("disputeOpened"), "info");
  }

  const currentStep = order && ORDER_STEPS.includes(order.status) ? order.status : order?.status ?? "CREATED";

  return (
    <>
      <PageShell size="wide">
        <PageHeader
          title={t("orderDetail")}
          subtitle={order ? `#${order.id.slice(0, 8)}` : undefined}
          actions={
            <Link href="/market/account" className="text-sm text-[var(--hp-accent)] hover:underline">
              {t("myAccount")}
            </Link>
          }
        />

        {loading && <SkeletonCard />}
        {order && (
          <div className="space-y-6">
            <Card>
              <div className="mb-4 overflow-x-auto">
                <StatusStepper
                  steps={ORDER_STEPS.map((s) => ({ id: s, label: s.replace(/_/g, " ") }))}
                  currentId={currentStep}
                />
              </div>
              <div className="flex flex-wrap gap-3 text-sm">
                <Badge variant="accent">{order.status}</Badge>
                <span className="font-mono text-[var(--hp-fg-muted)]">
                  {(order.amount_minor / 100).toFixed(2)} ₽
                </span>
              </div>
              {["IN_PROGRESS", "DELIVERED"].includes(order.status) && !disputeId && (
                <Button variant="secondary" className="mt-4" onClick={() => setShowDispute(true)}>
                  {t("openDispute")}
                </Button>
              )}
              {disputeId && (
                <Link href={`/market/disputes/${disputeId}`} className="mt-4 inline-block">
                  <Button variant="secondary">{t("viewDispute")}</Button>
                </Link>
              )}
            </Card>

            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <h3 className="mb-3 font-display font-semibold">{t("orderChat")}</h3>
                <ul className="mb-4 max-h-64 space-y-2 overflow-y-auto">
                  {messages.map((m) => (
                    <li
                      key={m.id}
                      className={`rounded-[var(--hp-radius)] p-2 text-sm ${
                        m.sender_id === myId ? "bg-[var(--hp-accent-muted)] ml-8" : "mr-8 border border-[var(--hp-border)]"
                      }`}
                    >
                      <span className="font-mono text-[10px] text-[var(--hp-fg-muted)]">{m.sender_id.slice(0, 8)}</span>
                      <p>{m.body}</p>
                    </li>
                  ))}
                  {messages.length === 0 && <p className="text-sm text-[var(--hp-fg-muted)]">{t("noMessages")}</p>}
                </ul>
                <div className="flex gap-2">
                  <Input value={messageText} onChange={(e) => setMessageText(e.target.value)} placeholder={t("messagePlaceholder")} />
                  <Button variant="primary" onClick={() => void postMessage()}>
                    {t("send")}
                  </Button>
                </div>
              </Card>

              <Card>
                <h3 className="mb-3 font-display font-semibold">{t("specVersions")}</h3>
                <ul className="mb-4 space-y-2 text-sm">
                  {specs.map((s) => (
                    <li key={s.id} className="rounded border border-[var(--hp-border)] p-2">
                      <span className="font-mono text-xs">v{s.version_number}</span>
                      <p className="mt-1 whitespace-pre-wrap text-[var(--hp-fg-muted)]">{s.spec_body}</p>
                    </li>
                  ))}
                </ul>
                <Textarea value={specText} onChange={(e) => setSpecText(e.target.value)} rows={4} label={t("newSpec")} />
                <Button variant="secondary" className="mt-2" onClick={() => void postSpec()}>
                  {t("saveSpec")}
                </Button>

                <h4 className="mb-2 mt-6 font-semibold">{t("deliverables")}</h4>
                <ul className="space-y-1 text-sm text-[var(--hp-fg-muted)]">
                  {deliverables.map((d) => (
                    <li key={d.id}>
                      #{d.revision_number} {d.description ?? "—"}
                    </li>
                  ))}
                  {deliverables.length === 0 && <li>{t("noDeliverables")}</li>}
                </ul>
              </Card>
            </div>
          </div>
        )}

        <Modal open={showDispute} onClose={() => setShowDispute(false)} title={t("openDispute")}>
          <Textarea value={disputeReason} onChange={(e) => setDisputeReason(e.target.value)} rows={4} label={t("disputeReason")} />
          <Button variant="primary" className="mt-3" onClick={() => void handleDispute()}>
            {t("openDispute")}
          </Button>
        </Modal>
      </PageShell>
      <Footer />
    </>
  );
}
