"use client";

import { useEffect, useState } from "react";
import { getKworkPreviewUrl } from "@/lib/api";
import { useTranslations } from "next-intl";

const CATEGORY_GRADIENT: Record<string, string> = {
  design: "from-violet-600/40 to-indigo-900/60",
  production: "from-cyan-600/40 to-slate-900/60",
  sound_engineering: "from-emerald-600/40 to-teal-900/60",
  songwriting: "from-amber-600/40 to-orange-900/60",
};

type KworkPreviewProps = {
  kworkId: string;
  category: string;
  hasCover: boolean;
  className?: string;
};

export function KworkPreview({ kworkId, category, hasCover, className = "" }: KworkPreviewProps) {
  const t = useTranslations("market");
  const [url, setUrl] = useState<string | null>(null);
  const gradient = CATEGORY_GRADIENT[category] ?? "from-[var(--hp-accent)]/30 to-[var(--hp-bg-subtle)]";

  useEffect(() => {
    if (!hasCover) return;
    void getKworkPreviewUrl(kworkId)
      .then((res) => setUrl(res.url))
      .catch(() => setUrl(null));
  }, [hasCover, kworkId]);

  return (
    <div
      className={`relative aspect-[16/9] overflow-hidden rounded-[var(--hp-radius)] bg-gradient-to-br ${gradient} ${className}`}
    >
      {url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={url} alt="" className="h-full w-full object-cover" />
      ) : (
        <div className="flex h-full flex-col items-center justify-center p-4 text-center">
          <span className="font-display text-xs font-semibold uppercase tracking-wider text-[var(--hp-fg-muted)]">
            {category.replace(/_/g, " ")}
          </span>
          {!hasCover && (
            <span className="mt-1 text-[10px] text-[var(--hp-fg-muted)]">{t("noPreview")}</span>
          )}
        </div>
      )}
    </div>
  );
}
