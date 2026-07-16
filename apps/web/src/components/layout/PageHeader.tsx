import type { ReactNode } from "react";
import { Badge } from "@hookpress/ui";

type PageHeaderProps = {
  title: string;
  subtitle?: string;
  badge?: string;
  badgeVariant?: "default" | "accent" | "success" | "warning";
  actions?: ReactNode;
};

export function PageHeader({ title, subtitle, badge, badgeVariant = "accent", actions }: PageHeaderProps) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="space-y-2">
        {badge && <Badge variant={badgeVariant}>{badge}</Badge>}
        <h1 className="font-display text-3xl font-bold tracking-tight text-[var(--hp-fg)] md:text-4xl">{title}</h1>
        {subtitle && <p className="max-w-2xl text-base text-[var(--hp-fg-muted)]">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
