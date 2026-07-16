import { Button, Badge, Card } from "@hookpress/ui";
import { Link } from "@/i18n/navigation";
import { getTranslations } from "next-intl/server";
import { Container } from "@/components/layout/Container";

const featureIcons = ["studio", "office", "market", "feed", "chat", "promo"] as const;
const stepNumbers = ["1", "2", "3", "4"] as const;
const statKeys = ["artists", "tracks", "orders", "campaigns"] as const;

function IconStudio() {
  return (
    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
    </svg>
  );
}

function IconOffice() {
  return (
    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  );
}

function IconMarket() {
  return (
    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  );
}

function IconFeed() {
  return (
    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
    </svg>
  );
}

function IconChat() {
  return (
    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  );
}

function IconPromo() {
  return (
    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  );
}

const featureIconMap = {
  studio: IconStudio,
  office: IconOffice,
  market: IconMarket,
  feed: IconFeed,
  chat: IconChat,
  promo: IconPromo,
};

export async function HomeLanding() {
  const t = await getTranslations("home");

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[var(--hp-gradient-hero)]" aria-hidden />
        <div className="hp-grid-pattern absolute inset-0 opacity-40" aria-hidden />

        <Container className="relative py-20 md:py-28 lg:py-32">
          <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
            <div className="animate-slide-up space-y-8">
              <Badge variant="accent">{t("heroBadge")}</Badge>
              <h1 className="text-4xl font-bold leading-[1.1] tracking-tight md:text-5xl lg:text-6xl">
                {t("heroTitle")}{" "}
                <span className="hp-gradient-text">{t("heroTitleAccent")}</span>
              </h1>
              <p className="max-w-xl text-lg leading-relaxed text-[var(--hp-fg-muted)]">{t("heroSubtitle")}</p>
              <div className="flex flex-wrap gap-3">
                <Link href="/login">
                  <Button variant="primary" size="lg">
                    {t("loginCta")}
                  </Button>
                </Link>
                <Link href="/studio">
                  <Button variant="secondary" size="lg">
                    {t("studioCta")}
                  </Button>
                </Link>
              </div>
              <div className="flex flex-wrap gap-6 pt-2 text-sm text-[var(--hp-fg-muted)]">
                <span className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-[var(--hp-success)]" />
                  {t("heroPoint1")}
                </span>
                <span className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-[var(--hp-success)]" />
                  {t("heroPoint2")}
                </span>
              </div>
            </div>

            <div className="relative animate-fade-in lg:pl-8">
              <div className="absolute -inset-4 rounded-[var(--hp-radius-xl)] bg-[var(--hp-accent)]/10 blur-3xl" aria-hidden />
              <Card padding="lg" className="relative animate-float border-[var(--hp-accent)]/20">
                <div className="mb-4 flex items-center justify-between">
                  <span className="text-sm font-medium text-[var(--hp-fg-muted)]">{t("previewTitle")}</span>
                  <Badge variant="success">{t("previewLive")}</Badge>
                </div>
                <div className="space-y-3">
                  <div className="rounded-[var(--hp-radius)] bg-[var(--hp-bg-subtle)] p-4">
                    <div className="mb-2 flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-[var(--hp-accent)]" />
                      <span className="text-xs font-medium">{t("previewProject")}</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-[var(--hp-border)]">
                      <div className="h-2 w-3/4 rounded-full bg-[var(--hp-gradient-accent)]" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] p-3">
                      <p className="text-xs text-[var(--hp-fg-muted)]">{t("previewLyrics")}</p>
                      <p className="mt-1 text-lg font-semibold">12</p>
                    </div>
                    <div className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] p-3">
                      <p className="text-xs text-[var(--hp-fg-muted)]">{t("previewScore")}</p>
                      <p className="mt-1 text-lg font-semibold">8.4</p>
                    </div>
                  </div>
                  <div className="flex gap-1 pt-1">
                    {Array.from({ length: 32 }).map((_, i) => (
                      <div
                        key={i}
                        className="w-1 rounded-full bg-[var(--hp-accent)]"
                        style={{ height: `${12 + Math.sin(i * 0.5) * 20 + 16}px`, opacity: 0.4 + (i % 5) * 0.12 }}
                      />
                    ))}
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </Container>
      </section>

      {/* Stats */}
      <section className="border-y border-[var(--hp-border)] bg-[var(--hp-bg-subtle)]">
        <Container className="py-10">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {statKeys.map((key) => (
              <div key={key} className="text-center md:text-left">
                <p className="text-3xl font-bold tracking-tight md:text-4xl">{t(`stats.${key}.value`)}</p>
                <p className="mt-1 text-sm text-[var(--hp-fg-muted)]">{t(`stats.${key}.label`)}</p>
              </div>
            ))}
          </div>
        </Container>
      </section>

      {/* Features */}
      <section className="hp-section">
        <Container>
          <div className="mx-auto mb-14 max-w-2xl text-center">
            <Badge variant="accent" className="mb-4">
              {t("featuresBadge")}
            </Badge>
            <h2 className="text-3xl font-bold tracking-tight md:text-4xl">{t("featuresTitle")}</h2>
            <p className="mt-4 text-[var(--hp-fg-muted)]">{t("featuresSubtitle")}</p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {featureIcons.map((key) => {
              const Icon = featureIconMap[key];
              return (
                <Link key={key} href={`/${key}`}>
                  <Card hover padding="lg" className="h-full">
                    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-[var(--hp-radius)] bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]">
                      <Icon />
                    </div>
                    <h3 className="text-lg font-semibold">{t(`features.${key}.title`)}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-[var(--hp-fg-muted)]">
                      {t(`features.${key}.description`)}
                    </p>
                    <p className="mt-4 text-sm font-medium text-[var(--hp-accent)]">{t("learnMore")} →</p>
                  </Card>
                </Link>
              );
            })}
          </div>
        </Container>
      </section>

      {/* How it works */}
      <section className="hp-section bg-[var(--hp-bg-subtle)]">
        <Container>
          <div className="mx-auto mb-14 max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight md:text-4xl">{t("howTitle")}</h2>
            <p className="mt-4 text-[var(--hp-fg-muted)]">{t("howSubtitle")}</p>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
            {stepNumbers.map((num, i) => (
              <div key={num} className="relative">
                {i < stepNumbers.length - 1 && (
                  <div
                    className="absolute left-1/2 top-8 hidden h-px w-full bg-[var(--hp-border)] lg:block"
                    aria-hidden
                  />
                )}
                <Card padding="lg" className="relative text-center lg:text-left">
                  <div className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-[var(--hp-accent)] text-sm font-bold text-white lg:mx-0">
                    {num}
                  </div>
                  <h3 className="font-semibold">{t(`how.step${num}.title`)}</h3>
                  <p className="mt-2 text-sm text-[var(--hp-fg-muted)]">{t(`how.step${num}.description`)}</p>
                </Card>
              </div>
            ))}
          </div>
        </Container>
      </section>

      {/* Audience */}
      <section className="hp-section">
        <Container>
          <div className="grid gap-8 lg:grid-cols-2">
            <Card padding="lg" className="border-[var(--hp-accent)]/20 bg-gradient-to-br from-[var(--hp-accent-muted)] to-transparent">
              <Badge variant="accent" className="mb-4">
                {t("forArtists.badge")}
              </Badge>
              <h3 className="text-2xl font-bold">{t("forArtists.title")}</h3>
              <ul className="mt-6 space-y-3">
                {(["1", "2", "3"] as const).map((n) => (
                  <li key={n} className="flex items-start gap-3 text-sm text-[var(--hp-fg-muted)]">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--hp-accent)]/20 text-xs text-[var(--hp-accent)]">
                      ✓
                    </span>
                    {t(`forArtists.point${n}`)}
                  </li>
                ))}
              </ul>
            </Card>

            <Card padding="lg" className="border-[var(--hp-border)]">
              <Badge className="mb-4">{t("forProducers.badge")}</Badge>
              <h3 className="text-2xl font-bold">{t("forProducers.title")}</h3>
              <ul className="mt-6 space-y-3">
                {(["1", "2", "3"] as const).map((n) => (
                  <li key={n} className="flex items-start gap-3 text-sm text-[var(--hp-fg-muted)]">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--hp-bg-subtle)] text-xs">
                      ✓
                    </span>
                    {t(`forProducers.point${n}`)}
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        </Container>
      </section>

      {/* CTA */}
      <section className="hp-section pb-24">
        <Container>
          <Card
            padding="lg"
            className="overflow-hidden border-[var(--hp-accent)]/30 bg-gradient-to-br from-[var(--hp-accent)]/10 via-[var(--hp-bg-elevated)] to-[var(--hp-bg-elevated)]"
          >
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight md:text-4xl">{t("ctaTitle")}</h2>
              <p className="mt-4 text-[var(--hp-fg-muted)]">{t("ctaSubtitle")}</p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <Link href="/login">
                  <Button variant="primary" size="lg">
                    {t("ctaButton")}
                  </Button>
                </Link>
                <Link href="/feed">
                  <Button variant="outline" size="lg">
                    {t("ctaSecondary")}
                  </Button>
                </Link>
              </div>
            </div>
          </Card>
        </Container>
      </section>
    </>
  );
}
