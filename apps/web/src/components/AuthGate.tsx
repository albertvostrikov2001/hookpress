"use client";

import { Button, Card } from "@hookpress/ui";
import { Link, usePathname } from "@/i18n/navigation";
import { getToken } from "@/lib/api";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState, type ReactNode } from "react";

type AuthGateProps = {
  children: ReactNode;
};

export function AuthGate({ children }: AuthGateProps) {
  const t = useTranslations("auth");
  const locale = useLocale();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(!!getToken());
    setReady(true);
  }, []);

  if (!ready) {
    return <p className="text-sm text-[var(--hp-fg-muted)]">{t("checking")}</p>;
  }

  if (!loggedIn) {
    const redirect = encodeURIComponent(`/${locale}${pathname}`);
    const loginHref = `/login?redirect=${redirect}`;

    return (
      <Card padding="lg" className="mx-auto max-w-md text-center">
        <h2 className="text-xl font-semibold">{t("required")}</h2>
        <p className="mt-2 text-sm text-[var(--hp-fg-muted)]">{t("requiredHint")}</p>
        <Link href={loginHref} className="mt-6 inline-block">
          <Button variant="primary">{t("signIn")}</Button>
        </Link>
      </Card>
    );
  }

  return <>{children}</>;
}
