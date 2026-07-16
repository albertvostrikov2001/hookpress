import { Badge, Card } from "@hookpress/ui";
import { useTranslations } from "next-intl";
import type { DistributionJob } from "@/lib/api";

type DistributionLogProps = {
  jobs: DistributionJob[];
};

export function DistributionLog({ jobs }: DistributionLogProps) {
  const t = useTranslations("office");

  if (jobs.length === 0) {
    return (
      <Card>
        <h3 className="mb-1 font-display text-lg font-semibold">{t("distributionTitle")}</h3>
        <p className="text-sm text-[var(--hp-fg-muted)]">{t("distributionEmpty")}</p>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="mb-4 font-display text-lg font-semibold">{t("distributionTitle")}</h3>
      <ul className="space-y-3">
        {jobs.map((job) => (
          <li
            key={job.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded-[var(--hp-radius)] border border-[var(--hp-border)] p-3 text-sm"
          >
            <div>
              <p className="font-medium">{job.provider}</p>
              <p className="font-mono text-xs text-[var(--hp-fg-muted)]">
                {job.external_id ?? job.id.slice(0, 8)}
              </p>
              {job.error_message && (
                <p className="mt-1 text-xs text-[var(--hp-danger)]">{job.error_message}</p>
              )}
            </div>
            <div className="text-right">
              <Badge variant={job.status === "SUCCEEDED" ? "success" : "accent"}>{job.status}</Badge>
              <p className="mt-1 font-mono text-[10px] text-[var(--hp-fg-muted)]">
                {new Date(job.created_at).toLocaleString()}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
