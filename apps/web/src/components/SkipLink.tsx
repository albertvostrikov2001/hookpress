"use client";

import { useTranslations } from "next-intl";

export function SkipLink() {
  const t = useTranslations("a11y");
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded-[var(--hp-radius)] focus:bg-[var(--hp-accent)] focus:px-4 focus:py-2 focus:text-white focus:outline-none focus:ring-2 focus:ring-white"
    >
      {t("skipToContent")}
    </a>
  );
}
