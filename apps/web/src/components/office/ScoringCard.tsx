import { Card } from "@hookpress/ui";
import { useTranslations } from "next-intl";
import type { ScoringReport } from "@/lib/api";

type ScoringCardProps = {
  reports: ScoringReport[];
};

export function ScoringCard({ reports }: ScoringCardProps) {
  const t = useTranslations("office");
  const report = reports[0];
  if (!report) {
    return (
      <Card>
        <p className="text-sm text-[var(--hp-fg-muted)]">{t("scoringEmpty")}</p>
      </Card>
    );
  }

  const raw = report.raw_json ?? {};
  const score = typeof raw.score === "number" ? raw.score : null;
  const confidence = typeof raw.confidence === "number" ? raw.confidence : null;
  const key = typeof raw.key === "string" ? raw.key : null;
  const dynamicRange = typeof raw.dynamic_range_db === "number" ? raw.dynamic_range_db : null;
  const spectral = typeof raw.spectral_centroid === "number" ? raw.spectral_centroid : null;

  const metrics = [
    { label: t("metricBpm"), value: report.bpm?.toFixed(1) ?? "—" },
    { label: t("metricKey"), value: key ?? "—" },
    { label: t("metricSpectral"), value: spectral != null ? String(spectral) : "—" },
    { label: t("metricDynamic"), value: dynamicRange != null ? `${dynamicRange} dB` : "—" },
    { label: t("metricScore"), value: score != null ? score.toFixed(2) : "—" },
    { label: t("metricConfidence"), value: confidence != null ? `${Math.round(confidence * 100)}%` : "—" },
  ];

  return (
    <Card>
      <h3 className="mb-1 font-display text-lg font-semibold">{t("scoringTitle")}</h3>
      <p className="mb-4 text-xs text-[var(--hp-fg-muted)]">{t("scoringDisclaimer")}</p>
      <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((m) => (
          <div key={m.label} className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-subtle)]/50 p-3">
            <dt className="text-xs text-[var(--hp-fg-muted)]">{m.label}</dt>
            <dd className="font-mono text-lg font-semibold tabular-nums text-[var(--hp-accent)]">{m.value}</dd>
          </div>
        ))}
      </dl>
      {Array.isArray(raw.reasons) && raw.reasons.length > 0 && (
        <ul className="mt-4 space-y-1 text-sm text-[var(--hp-fg-muted)]">
          {(raw.reasons as string[]).slice(0, 4).map((reason) => (
            <li key={reason}>• {reason}</li>
          ))}
        </ul>
      )}
    </Card>
  );
}
