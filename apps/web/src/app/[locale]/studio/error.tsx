"use client";

import { Button } from "@hookpress/ui";
import { useTranslations } from "next-intl";

export default function StudioError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const t = useTranslations("studio");
  const common = useTranslations("common");

  return (
    <main className="mx-auto max-w-4xl p-6 text-center">
      <h1 className="text-xl font-bold">{t("error")}</h1>
      <p className="mt-2 text-sm text-[var(--hp-fg-muted)]">{common("error")}</p>
      <Button variant="primary" className="mt-4" onClick={reset}>
        {common("retry")}
      </Button>
    </main>
  );
}
