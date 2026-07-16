"use client";

import { useEffect, useState } from "react";
import { Badge, Button, Card, SkeletonCard, useToast } from "@hookpress/ui";
import { KworkPortfolio } from "@/components/market/KworkPortfolio";
import { KworkPreview } from "@/components/market/KworkPreview";
import { MediaUploadPanel } from "@/components/media/MediaUploadPanel";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { Link, useRouter } from "@/i18n/navigation";
import { apiFetch, getKwork, getToken, payOrder, publishKwork, setKworkCover, type Kwork } from "@/lib/api";
import { useTranslations } from "next-intl";
import { useParams } from "next/navigation";

export default function KworkDetailPage() {
  const t = useTranslations("market");
  const tAuth = useTranslations("auth");
  const { toast } = useToast();
  const router = useRouter();
  const params = useParams();
  const kworkId = params.id as string;
  const [kwork, setKwork] = useState<Kwork | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        setKwork(await getKwork(kworkId));
      } catch (e) {
        setError(e instanceof Error ? e.message : t("error"));
      } finally {
        setLoading(false);
      }
    })();
  }, [kworkId, t]);

  async function orderKwork() {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    try {
      const orderRes = await apiFetch<{ id: string }>("/api/v1/market/orders", {
        method: "POST",
        body: JSON.stringify({ kwork_id: kworkId }),
      });
      await payOrder(orderRes.id);
      toast(t("orderCreated"), "success");
      router.push(`/market/orders/${orderRes.id}`);
    } catch (e) {
      toast(e instanceof Error ? e.message : t("error"), "error");
    }
  }

  async function handlePublish() {
    try {
      setKwork(await publishKwork(kworkId));
      toast(t("kworkPublished"), "success");
    } catch (e) {
      toast(e instanceof Error ? e.message : t("error"), "error");
    }
  }

  return (
    <>
      <PageShell size="narrow">
        <PageHeader
          title={kwork?.title ?? t("kworkDetail")}
          subtitle={kwork?.category}
          actions={
            <Link href="/market" className="text-sm text-[var(--hp-accent)] hover:underline">
              {t("backToMarket")}
            </Link>
          }
        />

        {loading && <SkeletonCard />}
        {error && (
          <Card>
            <p className="text-sm text-[var(--hp-danger)]">{error}</p>
          </Card>
        )}

        {kwork && (
          <div className="space-y-6">
            <KworkPreview
              kworkId={kwork.id}
              category={kwork.category}
              hasCover={Boolean(kwork.cover_asset_id)}
              className="max-h-48"
            />
            <Card>
              <div className="mb-4 flex flex-wrap items-center gap-2">
                <Badge variant="accent">{kwork.category}</Badge>
                <Badge>{kwork.status}</Badge>
              </div>
              <p className="text-[var(--hp-fg-muted)]">{kwork.description}</p>
              <p className="mt-4 font-display text-2xl font-semibold tabular-nums">
                {(kwork.price_minor / 100).toFixed(2)} ₽
              </p>
              {kwork.tags && kwork.tags.length > 0 && (
                <p className="mt-2 font-mono text-xs text-[var(--hp-fg-muted)]">{kwork.tags.join(" · ")}</p>
              )}
              <Link
                href={`/market/profiles/${kwork.profile_id}`}
                className="mt-4 inline-block text-sm text-[var(--hp-accent)] hover:underline"
              >
                {t("viewSellerProfile")}
              </Link>
            </Card>
            <Card padding="lg">
              <KworkPortfolio
                kworkId={kwork.id}
                assetIds={kwork.portfolio_asset_ids ?? []}
                editable={Boolean(getToken())}
                onUpdated={() => {
                  void getKwork(kworkId).then(setKwork);
                }}
              />
            </Card>
            <div className="flex flex-wrap gap-2">
              {getToken() && !kwork.cover_asset_id && (
                <MediaUploadPanel
                  accept="image/*"
                  label={t("uploadCover")}
                  onComplete={(assetId) => {
                    void setKworkCover(kworkId, assetId)
                      .then(setKwork)
                      .then(() => toast(t("coverUploaded"), "success"))
                      .catch((e) => toast(e instanceof Error ? e.message : t("error"), "error"));
                  }}
                  onError={(msg) => toast(msg, "error")}
                />
              )}
              {kwork.status === "DRAFT" && getToken() && (
                <Button variant="secondary" onClick={() => void handlePublish()}>
                  {t("publishKwork")}
                </Button>
              )}
              {getToken() ? (
                <Button variant="primary" onClick={() => void orderKwork()}>
                  {t("order")}
                </Button>
              ) : (
                <Link href="/login">
                  <Button variant="primary">{tAuth("loginToOrder")}</Button>
                </Link>
              )}
            </div>
          </div>
        )}
      </PageShell>
      <Footer />
    </>
  );
}
