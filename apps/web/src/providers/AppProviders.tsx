"use client";

import { ThemeProvider, ToastProvider } from "@hookpress/ui";
import { NextIntlClientProvider } from "next-intl";
import type { ReactNode } from "react";

type AppProvidersProps = {
  children: ReactNode;
  locale: string;
  messages: Record<string, unknown>;
};

export function AppProviders({ children, locale, messages }: AppProvidersProps) {
  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <ThemeProvider defaultTheme="dark">
        <ToastProvider>{children}</ToastProvider>
      </ThemeProvider>
    </NextIntlClientProvider>
  );
}
