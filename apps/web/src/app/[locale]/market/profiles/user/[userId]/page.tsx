"use client";

import { useEffect, useState } from "react";
import { Badge, Card, EmptyState, SkeletonCard } from "@hookpress/ui";
import { Footer } from "@/components/layout/Footer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageShell } from "@/components/layout/PageShell";
import { Link } from "@/i18n/navigation";
import { getKworkProfileByUser, type KworkProfile } from "@/lib/api";
import { useTranslations } from "next-intl";
import { useParams } from "next/navigation";

export default function MarketUserProfilePage() {
  const t = useTranslations("market");
  const params = useParams();
  const userId = params.userId as string;
  const [profile, setProfile] = useState<KworkProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        setProfile(await getKworkProfileByUser(userId));
      } catch (e) {
        setError(e instanceof Error ? e.message : t("profileNotFound"));
      } finally {
        setLoading(false);
      }
    })();
  }, [userId, t]);

  const kworks = profile?.kworks ?? [];

  return (
    <>
      <PageShell>
        <PageHeader
          title={profile?.title ?? t("performerProfile")}
          subtitle={profile?.bio ?? undefined}
          actions={
            profile ? (
              <Link href={`/market/profiles/${profile.id}`} className="text-sm text-[var(--hp-accent)] hover:underline">
                {t("viewFullProfile")}
              </Link>
            ) : undefined
          }
        />

        {loading && <SkeletonCard />}
        {error && !loading && (
          <Card>
            <p className="text-sm text-[var(--hp-fg-muted)]">{error}</p>
          </Card>
        )}

        {profile && (
          <div className="space-y-6">
            {profile.skills && profile.skills.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((skill) => (
                  <Badge key={skill} variant="accent">
                    {skill}
                  </Badge>
                ))}
              </div>
            )}

            <section>
              <h2 className="mb-3 font-display font-semibold">{t("profileKworks")}</h2>
              {kworks.length === 0 ? (
                <EmptyState title={t("noProfileKworks")} description={t("noProfileKworksHint")} />
              ) : (
                <ul className="grid gap-4 sm:grid-cols-2">
                  {kworks.map((k) => (
                    <li key={k.id}>
                      <Card padding="lg" hover>
                        <Link href={`/market/kworks/${k.id}`} className="font-display font-semibold hover:text-[var(--hp-accent)]">
                          {k.title}
                        </Link>
                        <p className="mt-1 text-sm text-[var(--hp-fg-muted)]">
                          {(k.price_minor / 100).toFixed(2)} ₽
                        </p>
                      </Card>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        )}
      </PageShell>
      <Footer />
    </>
  );
}
