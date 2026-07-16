"use client";

import { Link } from "@/i18n/navigation";
import { useTranslations } from "next-intl";
import { Container } from "./Container";

const productLinks = [
  { href: "/studio", key: "studio" as const },
  { href: "/office", key: "office" as const },
  { href: "/market", key: "market" as const },
  { href: "/feed", key: "feed" as const },
];

const communityLinks = [
  { href: "/chat", key: "chat" as const },
  { href: "/promo", key: "promo" as const },
  { href: "/charts", key: "charts" as const },
];

export function Footer() {
  const t = useTranslations("footer");
  const nav = useTranslations("nav");

  return (
    <footer className="mt-auto border-t border-[var(--hp-border)] bg-[var(--hp-bg-subtle)]">
      <Container className="py-12 md:py-16">
        <div className="grid gap-10 md:grid-cols-4">
          <div className="md:col-span-2">
            <Link href="/" className="inline-flex items-center gap-2 text-lg font-bold">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--hp-accent)] text-sm text-white">
                h
              </span>
              <span className="hp-gradient-text">hook.press</span>
            </Link>
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-[var(--hp-fg-muted)]">{t("tagline")}</p>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--hp-fg)]">
              {t("product")}
            </h3>
            <ul className="space-y-2.5">
              {productLinks.map((l) => (
                <li key={l.href}>
                  <Link
                    href={l.href}
                    className="text-sm text-[var(--hp-fg-muted)] transition hover:text-[var(--hp-accent)]"
                  >
                    {nav(l.key)}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--hp-fg)]">
              {t("community")}
            </h3>
            <ul className="space-y-2.5">
              {communityLinks.map((l) => (
                <li key={l.href}>
                  <Link
                    href={l.href}
                    className="text-sm text-[var(--hp-fg-muted)] transition hover:text-[var(--hp-accent)]"
                  >
                    {nav(l.key)}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-[var(--hp-border)] pt-8 sm:flex-row">
          <p className="text-xs text-[var(--hp-fg-muted)]">
            © {new Date().getFullYear()} hook.press · {t("rights")}
          </p>
          <div className="flex gap-6 text-xs text-[var(--hp-fg-muted)]">
            <span>{t("privacy")}</span>
            <span>{t("terms")}</span>
          </div>
        </div>
      </Container>
    </footer>
  );
}
