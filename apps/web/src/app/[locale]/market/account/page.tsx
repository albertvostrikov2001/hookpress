"use client";

import { useEffect, useState } from "react";
import { Badge, Button, Card, EmptyState, SkeletonCard } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { Link } from "@/i18n/navigation";
import {
  getMe,
  getWalletBalance,
  listMyOrders,
  listWalletEntries,
  type LedgerEntry,
  type MarketOrder,
} from "@/lib/api";
import { useTranslations } from "next-intl";

export default function MarketAccountPage() {
  const t = useTranslations("market");
  const [loading, setLoading] = useState(true);
  const [balanceMinor, setBalanceMinor] = useState<number | null>(null);
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [orders, setOrders] = useState<MarketOrder[]>([]);
  const [myId, setMyId] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const [wallet, ledger, mine, me] = await Promise.all([
          getWalletBalance(),
          listWalletEntries(),
          listMyOrders(),
          getMe(),
        ]);
        setBalanceMinor(wallet.balance_minor);
        setEntries(ledger);
        setOrders(mine);
        setMyId(me.id);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const buyerOrders = orders.filter((o) => o.buyer_id === myId);
  const sellerOrders = orders.filter((o) => o.seller_id === myId);

  return (
    <>
      <PageShell>
        <PageHeader title={t("myAccount")} subtitle={t("accountSubtitle")} />

        {loading && (
          <div className="grid gap-4 md:grid-cols-2">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        )}

        {!loading && (
          <div className="space-y-6">
            <Card>
              <p className="text-sm text-[var(--hp-fg-muted)]">{t("walletBalance")}</p>
              <p className="font-display text-3xl font-semibold tabular-nums">
                {balanceMinor !== null ? `${(balanceMinor / 100).toFixed(2)} ₽` : "—"}
              </p>
            </Card>

            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <h2 className="mb-3 font-display font-semibold">{t("ordersAsBuyer")}</h2>
                {buyerOrders.length === 0 ? (
                  <p className="text-sm text-[var(--hp-fg-muted)]">{t("noOrders")}</p>
                ) : (
                  <ul className="space-y-2">
                    {buyerOrders.map((o) => (
                      <li key={o.id}>
                        <Link href={`/market/orders/${o.id}`} className="flex items-center justify-between rounded border border-[var(--hp-border)] p-3 text-sm hover:border-[var(--hp-accent)]/40">
                          <span className="font-mono">{o.id.slice(0, 8)}…</span>
                          <Badge variant="accent">{o.status}</Badge>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>

              <Card>
                <h2 className="mb-3 font-display font-semibold">{t("ordersAsSeller")}</h2>
                {sellerOrders.length === 0 ? (
                  <p className="text-sm text-[var(--hp-fg-muted)]">{t("noOrders")}</p>
                ) : (
                  <ul className="space-y-2">
                    {sellerOrders.map((o) => (
                      <li key={o.id}>
                        <Link href={`/market/orders/${o.id}`} className="flex items-center justify-between rounded border border-[var(--hp-border)] p-3 text-sm hover:border-[var(--hp-accent)]/40">
                          <span className="font-mono">{o.id.slice(0, 8)}…</span>
                          <Badge variant="accent">{o.status}</Badge>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </div>

            <Card>
              <h2 className="mb-3 font-display font-semibold">{t("ledgerHistory")}</h2>
              {entries.length === 0 ? (
                <EmptyState title={t("noLedger")} description={t("noLedgerHint")} />
              ) : (
                <ul className="space-y-2 text-sm">
                  {entries.map((e) => (
                    <li key={e.id} className="flex items-center justify-between border-b border-[var(--hp-border)] py-2">
                      <div>
                        <p>{e.description}</p>
                        <p className="font-mono text-xs text-[var(--hp-fg-muted)]">{e.entry_type}</p>
                      </div>
                      <span className={`font-mono tabular-nums ${e.amount_minor >= 0 ? "text-[var(--hp-success)]" : "text-[var(--hp-danger)]"}`}>
                        {(e.amount_minor / 100).toFixed(2)} ₽
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        )}
      </PageShell>
      <Footer />
    </>
  );
}
