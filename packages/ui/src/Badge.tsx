import type { HTMLAttributes, ReactNode } from "react";

type BadgeVariant = "default" | "accent" | "success" | "warning";

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  children: ReactNode;
  variant?: BadgeVariant;
};

const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-[var(--hp-bg-subtle)] text-[var(--hp-fg-muted)]",
  accent: "bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]",
  success: "bg-[var(--hp-success)]/15 text-[var(--hp-success)]",
  warning: "bg-[var(--hp-warning)]/15 text-[var(--hp-warning)]",
};

export function Badge({ children, variant = "default", className = "", ...props }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
