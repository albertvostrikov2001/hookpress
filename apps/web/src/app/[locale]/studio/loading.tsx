import { getTranslations } from "next-intl/server";

export default async function StudioLoading() {
  const t = await getTranslations("studio");
  return (
    <main className="mx-auto max-w-4xl p-6">
      <p className="text-[var(--hp-fg-muted)]">{t("loading")}</p>
    </main>
  );
}
