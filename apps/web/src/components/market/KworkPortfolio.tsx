"use client";

import { useEffect, useState } from "react";
import { addKworkPortfolioAsset, getKworkPortfolioUrls } from "@/lib/api";
import { MediaUploadPanel } from "@/components/media/MediaUploadPanel";
import { useTranslations } from "next-intl";

type KworkPortfolioProps = {
  kworkId: string;
  assetIds: string[];
  editable?: boolean;
  onUpdated?: () => void;
};

export function KworkPortfolio({ kworkId, assetIds, editable, onUpdated }: KworkPortfolioProps) {
  const t = useTranslations("market");
  const [urls, setUrls] = useState<{ asset_id: string; url: string }[]>([]);

  useEffect(() => {
    if (assetIds.length === 0) {
      setUrls([]);
      return;
    }
    void getKworkPortfolioUrls(kworkId)
      .then((res) => setUrls(res.items.map((i) => ({ asset_id: i.asset_id, url: i.url }))))
      .catch(() => setUrls([]));
  }, [kworkId, assetIds.join(",")]);

  return (
    <div>
      <h3 className="mb-3 font-display font-semibold">{t("portfolio")}</h3>
      {urls.length > 0 ? (
        <ul className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
          {urls.map((item) => (
            <li key={item.asset_id} className="aspect-square overflow-hidden rounded-[var(--hp-radius)] border border-[var(--hp-border)]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={item.url} alt="" className="h-full w-full object-cover" />
            </li>
          ))}
        </ul>
      ) : (
        <p className="mb-4 text-sm text-[var(--hp-fg-muted)]">{t("portfolioEmpty")}</p>
      )}
      {editable && assetIds.length < 6 && (
        <MediaUploadPanel
          accept="image/*,audio/*"
          label={t("addPortfolioItem")}
          onComplete={(assetId) => {
            void addKworkPortfolioAsset(kworkId, assetId).then(() => onUpdated?.());
          }}
        />
      )}
    </div>
  );
}
