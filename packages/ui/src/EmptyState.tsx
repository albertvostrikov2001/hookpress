import type { ReactNode } from "react";
import { Button } from "./Button";

type EmptyStateProps = {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  actionHref?: string;
  icon?: ReactNode;
};

export function EmptyState({ title, description, actionLabel, onAction, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-[var(--hp-radius-lg)] border border-dashed border-[var(--hp-border)] bg-[var(--hp-bg-subtle)]/50 px-6 py-12 text-center">
      {icon && <div className="mb-4 text-[var(--hp-accent)]">{icon}</div>}
      <h3 className="font-display text-lg font-semibold text-[var(--hp-fg)]">{title}</h3>
      {description && <p className="mt-2 max-w-md text-sm text-[var(--hp-fg-muted)]">{description}</p>}
      {actionLabel && onAction && (
        <Button variant="primary" className="mt-6" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
