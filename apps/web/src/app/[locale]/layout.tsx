import { DM_Sans, JetBrains_Mono, Syne } from "next/font/google";
import { getMessages, getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import { Nav } from "@/components/Nav";
import { SkipLink } from "@/components/SkipLink";
import { routing, type Locale } from "@/i18n/routing";
import { AppProviders } from "@/providers/AppProviders";
import "../../../../../packages/ui/src/tokens.css";
import "../globals.css";

const syne = Syne({
  subsets: ["latin", "latin-ext"],
  variable: "--font-display",
  display: "swap",
});

const dmSans = DM_Sans({
  subsets: ["latin", "latin-ext"],
  variable: "--font-body",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin", "cyrillic"],
  variable: "--font-mono",
  display: "swap",
});

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "home" });
  return {
    title: `${t("title")} — ${t("heroTitleAccent")}`,
    description: t("heroSubtitle"),
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!routing.locales.includes(locale as Locale)) notFound();

  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <body className={`${syne.variable} ${dmSans.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
        <AppProviders locale={locale} messages={messages}>
          <SkipLink />
          <Nav />
          <main id="main-content" tabIndex={-1}>
            {children}
          </main>
        </AppProviders>
      </body>
    </html>
  );
}
