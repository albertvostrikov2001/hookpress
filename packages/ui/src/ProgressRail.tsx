type ProgressRailProps = {
  value: number;
  max?: number;
  label?: string;
  showValue?: boolean;
  variant?: "default" | "success" | "warning" | "danger";
  size?: "sm" | "md";
};

const fillClass: Record<NonNullable<ProgressRailProps["variant"]>, string> = {
  default: "bg-[var(--hp-accent)]",
  success: "bg-[var(--hp-success)]",
  warning: "bg-[var(--hp-warning)]",
  danger: "bg-[var(--hp-danger)]",
};

export function ProgressRail({
  value,
  max = 100,
  label,
  showValue = true,
  variant = "default",
  size = "md",
}: ProgressRailProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const height = size === "sm" ? "h-1.5" : "h-2.5";

  return (
    <div className="space-y-1.5" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={max} aria-label={label}>
      {(label || showValue) && (
        <div className="flex items-center justify-between gap-2 text-xs">
          {label && <span className="text-[var(--hp-fg-muted)]">{label}</span>}
          {showValue && <span className="font-mono tabular-nums text-[var(--hp-fg-muted)]">{Math.round(pct)}%</span>}
        </div>
      )}
      <div className={`relative overflow-hidden rounded-full bg-[var(--hp-bg-subtle)] ${height}`}>
        <div
          className={`absolute inset-y-0 left-0 rounded-full transition-all duration-500 ease-out ${fillClass[variant]}`}
          style={{ width: `${pct}%`, boxShadow: pct > 0 ? `0 0 12px var(--hp-glow)` : undefined }}
        />
        <div
          className="pointer-events-none absolute inset-y-0 w-px bg-[var(--hp-signal)]/40"
          style={{ left: `${Math.min(pct, 98)}%` }}
          aria-hidden
        />
      </div>
    </div>
  );
}
