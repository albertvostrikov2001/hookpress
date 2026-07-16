"use client";

import { useEffect, useState } from "react";
import { Badge, Button, Card, EmptyState, Input, SkeletonCard } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { getMe, listAuditLogs, type AuditLog } from "@/lib/api";
import { useTranslations } from "next-intl";

const PAGE_SIZE = 30;

export default function AdminAuditPage() {
  const t = useTranslations("admin");
  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [actionPrefix, setActionPrefix] = useState("");

  async function load(nextOffset = 0, append = false) {
    setLoading(true);
    try {
      const data = await listAuditLogs({
        limit: PAGE_SIZE,
        offset: nextOffset,
        actionPrefix: actionPrefix || undefined,
      });
      setLogs(append ? (prev) => [...prev, ...data.items] : data.items);
      setTotal(data.total);
      setHasMore(data.has_more);
      setOffset(nextOffset);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void getMe()
      .then((me) => setAllowed(me.roles.some((r) => r === "admin" || r === "moderator")))
      .catch(() => setAllowed(false));
  }, []);

  useEffect(() => {
    if (allowed) void load(0, false);
  }, [allowed]);

  if (allowed === null) {
    return (
      <PageShell size="wide">
        <SkeletonCard />
      </PageShell>
    );
  }

  if (!allowed) {
    return (
      <>
        <PageShell size="wide">
          <PageHeader title={t("auditTitle")} />
          <Card>
            <p className="text-[var(--hp-danger)]">{t("auditNoAccess")}</p>
          </Card>
        </PageShell>
        <Footer />
      </>
    );
  }

  return (
    <>
      <PageShell size="wide">
        <PageHeader title={t("auditTitle")} subtitle={t("auditSubtitle")} badge="Admin" />

        <Card className="mb-6">
          <div className="flex flex-wrap gap-2">
            <Input
              value={actionPrefix}
              onChange={(e) => setActionPrefix(e.target.value)}
              placeholder={t("auditFilter")}
              className="max-w-xs flex-1"
            />
            <Button variant="primary" onClick={() => void load(0, false)}>
              {t("auditSearch")}
            </Button>
          </div>
          <p className="mt-2 font-mono text-xs text-[var(--hp-fg-muted)]">
            {t("auditTotal")}: {total}
          </p>
        </Card>

        {loading && logs.length === 0 && <SkeletonCard />}

        {logs.length === 0 && !loading && (
          <EmptyState title={t("auditEmpty")} description={t("auditEmptyHint")} />
        )}

        <ul className="space-y-2">
          {logs.map((log) => (
            <li key={log.id}>
              <Card padding="sm">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <p className="font-mono text-sm font-medium text-[var(--hp-accent)]">{log.action}</p>
                    <p className="text-xs text-[var(--hp-fg-muted)]">
                      {log.resource_type}
                      {log.resource_id ? ` · ${log.resource_id}` : ""}
                    </p>
                    {log.metadata_json && Object.keys(log.metadata_json).length > 0 && (
                      <pre className="mt-2 max-h-24 overflow-auto rounded bg-[var(--hp-bg-subtle)] p-2 font-mono text-[10px] text-[var(--hp-fg-muted)]">
                        {JSON.stringify(log.metadata_json, null, 2)}
                      </pre>
                    )}
                  </div>
                  <div className="text-right text-xs text-[var(--hp-fg-muted)]">
                    <Badge variant="accent">{log.ip_address ?? "—"}</Badge>
                    <p className="mt-1 font-mono">{new Date(log.created_at).toLocaleString()}</p>
                  </div>
                </div>
              </Card>
            </li>
          ))}
        </ul>

        {hasMore && (
          <Button variant="secondary" className="mt-4" disabled={loading} onClick={() => void load(offset + PAGE_SIZE, true)}>
            {t("auditLoadMore")}
          </Button>
        )}
      </PageShell>
      <Footer />
    </>
  );
}
