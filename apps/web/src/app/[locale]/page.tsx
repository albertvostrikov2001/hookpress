import { HomeLanding } from "@/components/home/HomeLanding";
import { Footer } from "@/components/layout/Footer";
import { setRequestLocale } from "next-intl/server";

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <div className="flex min-h-[calc(100vh-64px)] flex-col">
      <HomeLanding />
      <Footer />
    </div>
  );
}
