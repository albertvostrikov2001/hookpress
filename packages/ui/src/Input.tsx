import type { InputHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
  hint?: string;
};

export function Input({ label, error, hint, className = "", id, ...props }: InputProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");

  return (
    <label className="block space-y-1.5" htmlFor={inputId}>
      {label && <span className="text-sm text-[var(--hp-fg-muted)]">{label}</span>}
      <input
        id={inputId}
        className={`w-full rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] px-3 py-2 text-sm text-[var(--hp-fg)] placeholder:text-[var(--hp-fg-muted)] transition focus:border-[var(--hp-accent)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--hp-accent)]/20 ${className}`}
        {...props}
      />
      {error && <span className="text-xs text-[var(--hp-danger)]">{error}</span>}
      {hint && !error && <span className="text-xs text-[var(--hp-fg-muted)]">{hint}</span>}
    </label>
  );
}
