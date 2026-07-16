"use client";

import { useTheme } from "@hookpress/ui";
import { useTranslations } from "next-intl";

export function ThemeSwitcher() {
  const { theme, toggleTheme } = useTheme();
  const t = useTranslations("nav");

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="rounded-md border border-[var(--hp-border)] px-2 py-1 text-xs text-[var(--hp-fg-muted)] hover:text-[var(--hp-fg)]"
      title={t("theme")}
    >
      {theme === "dark" ? "☀" : "☾"}
    </button>
  );
}
