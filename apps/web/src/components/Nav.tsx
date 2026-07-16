"use client";

import { Link, usePathname, useRouter } from "@/i18n/navigation";
import { Badge, Button } from "@hookpress/ui";
import { NavMenu } from "@/components/nav/NavMenu";
import { getMe, getToken, listNotifications, logout, type User } from "@/lib/api";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";
import { Container } from "./layout/Container";
import { LocaleSwitcher } from "./LocaleSwitcher";
import { NotificationsBell } from "./NotificationsBell";
import { ThemeSwitcher } from "./ThemeSwitcher";

const coreLinks = [
  { href: "/studio", key: "studio" as const },
  { href: "/office", key: "office" as const },
  { href: "/market", key: "market" as const },
  { href: "/feed", key: "feed" as const },
  { href: "/charts", key: "charts" as const },
  { href: "/chat", key: "chat" as const },
];

const moreLinks = [
  { href: "/promo", key: "promo" as const },
  { href: "/dashboard", key: "dashboard" as const, authOnly: true },
];

function navLinkClass(active: boolean) {
  return `rounded-[var(--hp-radius)] px-2.5 py-2 text-sm font-medium transition ${
    active
      ? "bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]"
      : "text-[var(--hp-fg-muted)] hover:bg-[var(--hp-bg-subtle)] hover:text-[var(--hp-fg)]"
  }`;
}

function userInitials(user: User | null): string {
  if (!user?.display_name) return "?";
  const parts = user.display_name.trim().split(/\s+/);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  return user.display_name.slice(0, 2).toUpperCase();
}

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const t = useTranslations("nav");
  const ta = useTranslations("a11y");
  const [loggedIn, setLoggedIn] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [unread, setUnread] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const token = getToken();
    setLoggedIn(!!token);
    if (!token) {
      setUser(null);
      setUnread(0);
      return;
    }
    void getMe()
      .then(setUser)
      .catch(() => {
        setUser(null);
        setLoggedIn(false);
      });
    void listNotifications()
      .then((data) => setUnread(data.unread_count))
      .catch(() => setUnread(0));
  }, [pathname]);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  const roles = user?.roles ?? [];
  const isModerator = roles.includes("moderator") || roles.includes("admin");
  const isAdmin = roles.includes("admin");

  const visibleMore = moreLinks.filter((l) => !l.authOnly || loggedIn);
  const moreItems = visibleMore.map((l) => ({ href: l.href, label: t(l.key) }));
  const moreActive = visibleMore.some((l) => pathname.startsWith(l.href));

  const accountItems = useMemo(() => {
    if (!loggedIn) return [];
    return [
      { href: "/profile", label: t("profile") },
      { href: "/notifications", label: t("notifications") },
    ];
  }, [loggedIn, t]);

  const adminItems = useMemo(() => {
    const items: { href: string; label: string }[] = [];
    if (isModerator) items.push({ href: "/moderator", label: t("moderator") });
    if (isAdmin || isModerator) {
      items.push({ href: "/admin/feed", label: t("admin") });
      items.push({ href: "/admin/audit", label: t("auditAdmin") });
    }
    if (isAdmin) items.push({ href: "/admin/charts", label: t("chartsAdmin") });
    return items;
  }, [isAdmin, isModerator, t]);

  const adminActive = adminItems.some((l) => pathname.startsWith(l.href));
  const accountActive = accountItems.some((l) => pathname.startsWith(l.href));

  const mobileSections = useMemo(() => {
    const sections: { title: string; links: { href: string; label: string }[] }[] = [
      {
        title: t("sectionProduct"),
        links: [
          ...coreLinks.map((l) => ({ href: l.href, label: t(l.key) })),
          ...moreItems,
        ],
      },
    ];
    if (loggedIn) {
      sections.push({
        title: t("sectionAccount"),
        links: [...accountItems, { href: "/login", label: t("logout") }],
      });
    }
    if (adminItems.length > 0) {
      sections.push({ title: t("sectionAdmin"), links: adminItems });
    }
    return sections;
  }, [accountItems, adminItems, loggedIn, moreItems, t]);

  function handleLogout() {
    void logout().finally(() => router.push("/login"));
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = search.trim();
    if (q) router.push(`/market?q=${encodeURIComponent(q)}`);
    else router.push("/market");
  }

  const roleLabel =
    roles.includes("artist") && roles.includes("performer")
      ? t("roleArtistPerformer")
      : roles[0] ?? "user";

  return (
    <header className="sticky top-0 z-50 isolate hp-glass">
      <Container>
        <div className="flex h-16 items-center gap-2 lg:gap-3">
          <Link href="/" className="flex shrink-0 items-center gap-2.5 font-display font-bold">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--hp-accent)] text-sm text-[var(--hp-accent-fg)] shadow-sm shadow-[var(--hp-glow)]">
              h
            </span>
            <span className="hidden sm:inline hp-gradient-text">hook.press</span>
          </Link>

          <nav
            className="hidden min-w-0 flex-1 items-center lg:flex"
            aria-label={ta("mainNav")}
          >
            <div
              className="flex min-w-0 flex-1 items-center gap-0.5 overflow-x-auto pr-1 [&::-webkit-scrollbar]:hidden"
              style={{ scrollbarWidth: "none" }}
            >
              {coreLinks.map((l) => {
                const active = pathname.startsWith(l.href);
                return (
                  <Link key={l.href} href={l.href} className={`shrink-0 whitespace-nowrap ${navLinkClass(active)}`}>
                    {t(l.key)}
                  </Link>
                );
              })}
            </div>
          </nav>

          <div className="relative z-20 flex shrink-0 items-center gap-1 border-[var(--hp-border)] sm:gap-1.5 lg:border-l lg:pl-2 xl:gap-2">
            {moreItems.length > 0 && (
              <NavMenu label={t("more")} items={moreItems} pathname={pathname} active={moreActive} />
            )}
            {adminItems.length > 0 && (
              <NavMenu
                label={t("adminMenu")}
                items={adminItems}
                pathname={pathname}
                active={adminActive}
              />
            )}
            <form onSubmit={handleSearch} className="hidden w-36 shrink-0 xl:block">
              <label className="sr-only" htmlFor="global-search">
                {t("search")}
              </label>
              <input
                id="global-search"
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t("searchPlaceholderShort")}
                className="w-full rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] px-3 py-2 text-sm text-[var(--hp-fg)] placeholder:text-[var(--hp-fg-muted)] focus:border-[var(--hp-accent)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--hp-accent)]/20"
              />
            </form>
            <div className="hidden items-center gap-1 sm:flex">
              <LocaleSwitcher />
              <ThemeSwitcher />
            </div>
            {loggedIn && <NotificationsBell onUnreadChange={setUnread} />}
            {loggedIn && unread > 0 && (
              <Link href="/notifications" className="relative sm:hidden">
                <span className="sr-only">{t("notifications")}</span>
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-[var(--hp-radius)] border border-[var(--hp-border)] text-sm">
                  🔔
                </span>
                <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--hp-signal)] px-1 text-[10px] font-bold text-white">
                  {unread > 9 ? "9+" : unread}
                </span>
              </Link>
            )}
            {loggedIn && user ? (
              <NavMenu
                label={t("accountMenu")}
                items={accountItems}
                pathname={pathname}
                active={accountActive}
                align="end"
                triggerClassName="!px-1.5"
                actions={[{ label: t("logout"), onClick: handleLogout }]}
              >
                <span className="flex items-center gap-2">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--hp-accent-muted)] text-xs font-semibold text-[var(--hp-accent)]">
                    {userInitials(user)}
                  </span>
                  <span className="hidden max-w-[7rem] truncate text-left xl:inline">{user.display_name}</span>
                </span>
              </NavMenu>
            ) : (
              <Link href="/login" className="hidden sm:block">
                <Button variant="primary" size="sm">
                  {t("login")}
                </Button>
              </Link>
            )}
            <button
              type="button"
              className="inline-flex h-10 w-10 items-center justify-center rounded-[var(--hp-radius)] border border-[var(--hp-border)] text-[var(--hp-fg-muted)] lg:hidden"
              aria-label={t("menu")}
              aria-expanded={mobileOpen}
              onClick={() => setMobileOpen((v) => !v)}
            >
              {mobileOpen ? "✕" : "☰"}
            </button>
          </div>
        </div>

        {mobileOpen && (
          <nav className="border-t border-[var(--hp-border)] py-4 lg:hidden">
            <form onSubmit={handleSearch} className="mb-4 px-1">
              <input
                type="search"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t("searchPlaceholder")}
                className="w-full rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] px-3 py-2 text-sm"
              />
            </form>
            {loggedIn && user && (
              <div className="mb-4 flex items-center gap-3 px-1">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--hp-accent-muted)] text-xs font-semibold text-[var(--hp-accent)]">
                  {userInitials(user)}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{user.display_name}</p>
                  <Badge variant="accent" className="mt-1 font-mono text-[10px]">
                    {roleLabel}
                  </Badge>
                </div>
              </div>
            )}
            <div className="space-y-4">
              {mobileSections.map((section) => (
                <div key={section.title}>
                  <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wide text-[var(--hp-fg-muted)]">
                    {section.title}
                  </p>
                  <div className="flex flex-col gap-0.5">
                    {section.links.map((l) => {
                      if (l.href === "/login" && loggedIn) {
                        return (
                          <button
                            key="logout"
                            type="button"
                            onClick={handleLogout}
                            className="rounded-[var(--hp-radius)] px-3 py-2.5 text-left text-sm font-medium text-[var(--hp-fg-muted)] hover:bg-[var(--hp-bg-subtle)]"
                          >
                            {l.label}
                          </button>
                        );
                      }
                      const active = pathname.startsWith(l.href);
                      return (
                        <Link
                          key={l.href}
                          href={l.href}
                          className={`rounded-[var(--hp-radius)] px-3 py-2.5 text-sm font-medium ${
                            active ? "bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]" : "text-[var(--hp-fg-muted)]"
                          }`}
                        >
                          {l.label}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-2 border-t border-[var(--hp-border)] pt-4">
              <LocaleSwitcher />
              <ThemeSwitcher />
              {!loggedIn && (
                <Link href="/login">
                  <Button variant="primary" size="sm">
                    {t("login")}
                  </Button>
                </Link>
              )}
            </div>
          </nav>
        )}
      </Container>
    </header>
  );
}
