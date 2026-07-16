"use client";

import { useEffect, useState } from "react";
import { Button, Card, EmptyState, Input, Modal, useToast } from "@hookpress/ui";
import { KworkPreview } from "@/components/market/KworkPreview";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { Link } from "@/i18n/navigation";
import {
  apiFetch,
  buildKworksQuery,
  getToken,
  openDispute,
  payOrder,
  type Kwork,
  type MarketOrder,
} from "@/lib/api";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";

const CATEGORIES = ["design", "production", "sound_engineering", "songwriting"] as const;

export default function MarketPage() {
  const t = useTranslations("market");
  const tAuth = useTranslations("auth");
  const tc = useTranslations("common");
  const { toast } = useToast();
  const searchParams = useSearchParams();
  const [loggedIn, setLoggedIn] = useState(false);
  const [kworks, setKworks] = useState<Kwork[]>([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [price, setPrice] = useState("500000");
  const [query, setQuery] = useState(searchParams.get("q") ?? "");
  const [category, setCategory] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<MarketOrder | null>(null);
  const [disputeReason, setDisputeReason] = useState("");
  const [showDispute, setShowDispute] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await apiFetch<Kwork[]>(buildKworksQuery({ q: query || undefined, category: category || undefined }));
      setKworks(Array.isArray(data) ? data : []);
    } catch (e) {
      toast(e instanceof Error ? e.message : t("error"), "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLoggedIn(!!getToken());
  }, []);

  useEffect(() => {
    void load();
  }, [query, category]);

  async function createKwork() {
    await apiFetch("/api/v1/market/kworks", {
      method: "POST",
      body: JSON.stringify({
        title,
        description: "Demo kwork",
        category: category || "design",
        price_minor: parseInt(price, 10),
      }),
    });
    setTitle("");
    await load();
    toast(t("kworkCreated"), "success");
  }

  async function order(kworkId: string) {
    const orderRes = await apiFetch<{ id: string }>("/api/v1/market/orders", {
      method: "POST",
      body: JSON.stringify({ kwork_id: kworkId }),
    });
    await payOrder(orderRes.id);
    const detail = await apiFetch<MarketOrder>(`/api/v1/market/orders/${orderRes.id}`);
    setSelectedOrder(detail);
    toast(t("orderCreated"), "success");
  }

  async function handleDispute() {
    if (!selectedOrder || !disputeReason.trim()) return;
    await openDispute(selectedOrder.id, disputeReason);
    setShowDispute(false);
    setDisputeReason("");
    setSelectedOrder(await apiFetch<MarketOrder>(`/api/v1/market/orders/${selectedOrder.id}`));
    toast(t("disputeOpened"), "info");
  }

  return (
    <div className="flex min-h-[calc(100vh-64px)] flex-col">
      <PageShell size="wide">
        <PageHeader
          title={t("title")}
          badge="Market"
          actions={
            loggedIn ? (
              <Link href="/market/account">
                <Button variant="secondary" size="sm">
                  {t("myAccount")}
                </Button>
              </Link>
            ) : undefined
          }
        />

        {loggedIn ? (
          <Card padding="lg" className="mb-6">
            <h2 className="mb-4 font-display font-semibold">{t("createKwork")}</h2>
            <div className="grid gap-3 md:grid-cols-2">
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder={t("titlePlaceholder")} />
              <Input value={price} onChange={(e) => setPrice(e.target.value)} placeholder={t("pricePlaceholder")} />
            </div>
            <Button variant="primary" className="mt-4" onClick={() => void createKwork()} disabled={!title}>
              {t("publish")}
            </Button>
          </Card>
        ) : (
          <Card padding="lg" className="mb-6 text-center">
            <p className="text-sm text-[var(--hp-fg-muted)]">{tAuth("loginToCreate")}</p>
            <Link href="/login" className="mt-4 inline-block">
              <Button variant="primary">{tAuth("signIn")}</Button>
            </Link>
          </Card>
        )}

        <Card padding="lg" className="mb-6">
          <h2 className="mb-4 font-display font-semibold">{t("filters")}</h2>
          <div className="grid gap-3 md:grid-cols-2">
            <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t("searchPlaceholder")} />
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] px-3 py-2 text-sm"
            >
              <option value="">{t("allCategories")}</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {t(`categories.${c}` as "categories.design")}
                </option>
              ))}
            </select>
          </div>
        </Card>

        {loading && <p className="text-sm text-[var(--hp-fg-muted)]">{tc("loading")}</p>}
        {!loading && kworks.length === 0 && (
          <EmptyState title={t("emptyKworks")} description={t("emptyKworksHint")} />
        )}

        <ul className="grid gap-4 sm:grid-cols-2">
          {kworks.map((k) => (
            <li key={k.id}>
              <Card padding="lg" hover className="flex h-full flex-col justify-between gap-4 overflow-hidden">
                <KworkPreview kworkId={k.id} category={k.category} hasCover={Boolean(k.cover_asset_id)} />
                <div>
                  <Link href={`/market/kworks/${k.id}`} className="font-display font-semibold hover:text-[var(--hp-accent)]">
                    {k.title}
                  </Link>
                  <p className="mt-1 text-sm text-[var(--hp-fg-muted)]">
                    {k.category} · {(k.price_minor / 100).toFixed(2)} ₽
                  </p>
                  <p className="mt-2 line-clamp-2 text-sm text-[var(--hp-fg-muted)]">{k.description}</p>
                </div>
                <div className="flex gap-2">
                  <Link href={`/market/kworks/${k.id}`}>
                    <Button variant="secondary" size="sm">
                      {t("viewKwork")}
                    </Button>
                  </Link>
                  {loggedIn ? (
                    <Button variant="primary" size="sm" onClick={() => void order(k.id)}>
                      {t("order")}
                    </Button>
                  ) : (
                    <Link href="/login">
                      <Button variant="outline" size="sm">
                        {tAuth("loginToOrder")}
                      </Button>
                    </Link>
                  )}
                </div>
              </Card>
            </li>
          ))}
        </ul>

        <Modal open={showDispute} onClose={() => setShowDispute(false)} title={t("openDispute")}>
          <Input value={disputeReason} onChange={(e) => setDisputeReason(e.target.value)} placeholder={t("disputeReason")} />
          <Button variant="primary" className="mt-3" onClick={() => void handleDispute()}>
            {t("openDispute")}
          </Button>
        </Modal>
      </PageShell>
      <Footer />
    </div>
  );
}
