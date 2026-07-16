type Step = {
  id: string;
  label: string;
};

type StatusStepperProps = {
  steps: Step[];
  currentId: string;
  failedId?: string;
};

export function StatusStepper({ steps, currentId, failedId }: StatusStepperProps) {
  const currentIndex = steps.findIndex((s) => s.id === currentId);
  const failedIndex = failedId ? steps.findIndex((s) => s.id === failedId) : -1;

  return (
    <ol className="flex flex-wrap items-center gap-2" aria-label="Progress">
      {steps.map((step, index) => {
        const isComplete = index < currentIndex;
        const isCurrent = step.id === currentId;
        const isFailed = step.id === failedId;
        let dotClass = "bg-[var(--hp-bg-subtle)] border-[var(--hp-border)] text-[var(--hp-fg-muted)]";
        if (isFailed) dotClass = "bg-[var(--hp-danger)]/15 border-[var(--hp-danger)] text-[var(--hp-danger)]";
        else if (isComplete) dotClass = "bg-[var(--hp-success)]/15 border-[var(--hp-success)] text-[var(--hp-success)]";
        else if (isCurrent) dotClass = "bg-[var(--hp-accent-muted)] border-[var(--hp-accent)] text-[var(--hp-accent)]";

        return (
          <li key={step.id} className="flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${dotClass}`}
            >
              <span className="font-mono text-[10px] opacity-70">{String(index + 1).padStart(2, "0")}</span>
              {step.label}
            </span>
            {index < steps.length - 1 && (
              <span
                className={`hidden h-px w-6 sm:block ${index < currentIndex ? "bg-[var(--hp-accent)]" : "bg-[var(--hp-border)]"}`}
                aria-hidden
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}
