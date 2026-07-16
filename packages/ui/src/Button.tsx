import type { ButtonHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "outline";
type ButtonSize = "sm" | "md" | "lg";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
};

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--hp-accent)] text-[var(--hp-accent-fg)] hover:bg-[var(--hp-accent-hover)] shadow-sm shadow-[var(--hp-glow)]",
  secondary:
    "bg-[var(--hp-bg-subtle)] text-[var(--hp-fg)] border border-[var(--hp-border)] hover:bg-[var(--hp-bg-elevated)] hover:border-[var(--hp-accent)]/30",
  ghost: "bg-transparent text-[var(--hp-fg-muted)] hover:bg-[var(--hp-accent-muted)] hover:text-[var(--hp-fg)]",
  outline:
    "bg-transparent text-[var(--hp-accent)] border border-[var(--hp-accent)]/40 hover:bg-[var(--hp-accent-muted)]",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-[var(--hp-radius)] font-medium transition-all duration-200 disabled:pointer-events-none disabled:opacity-50 ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
