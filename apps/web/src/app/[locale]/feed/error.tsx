"use client";

import { Button } from "@hookpress/ui";
import { useTranslations } from "next-intl";

export default function FeedError({ reset }: { error: Error; reset: () => void }) {
  const t = useTranslations("feed");
  const common = useTranslations("common");

  return (
    <main className="mx-auto max-w-4xl p-6 text-center">
      <h1 className="text-xl font-bold">{t("error")}</h1>
      <Button variant="primary" className="mt-4" onClick={reset}>
        {common("retry")}
      </Button>
    </main>
  );
}
