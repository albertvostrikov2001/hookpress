"use client";

import { Suspense, useState } from "react";
import { Button, Card, Input } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { devLogin } from "@/lib/api";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";

function LoginForm() {
  const searchParams = useSearchParams();
  const t = useTranslations("login");
  const [email, setEmail] = useState("artist@example.com");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const sessionExpired = searchParams.get("reason") === "session_expired";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await devLogin(email);
      const redirect = searchParams.get("redirect");
      if (redirect && redirect.startsWith("/")) {
        window.location.assign(redirect);
        return;
      }
      window.location.assign(`/${window.location.pathname.match(/^\/(ru|en)/)?.[1] ?? "ru"}/studio`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell size="narrow">
      <div className="mx-auto max-w-md">
        <PageHeader title={t("title")} subtitle={t("subtitle")} badge="Dev" />
        <Card padding="lg">
          <p className="mb-6 text-sm text-[var(--hp-fg-muted)]">{t("devHint")}</p>
          {sessionExpired && (
            <p className="mb-4 rounded-[var(--hp-radius)] border border-[var(--hp-warning)]/30 bg-[var(--hp-warning)]/10 px-3 py-2 text-sm text-[var(--hp-fg)]">
              {t("sessionExpired")}
            </p>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              type="email"
              label={t("email")}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            {error && <p className="text-sm text-[var(--hp-danger)]">{error}</p>}
            <Button variant="primary" className="w-full" disabled={loading} type="submit">
              {loading ? "…" : t("submit")}
            </Button>
          </form>
        </Card>
      </div>
      <Footer />
    </PageShell>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <PageShell size="narrow">
          <p className="text-[var(--hp-fg-muted)]">…</p>
        </PageShell>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
