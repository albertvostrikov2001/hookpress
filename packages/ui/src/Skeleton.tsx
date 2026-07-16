type SkeletonProps = {
  className?: string;
};

export function Skeleton({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded-[var(--hp-radius)] bg-[var(--hp-bg-subtle)] ${className}`}
      aria-hidden
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="space-y-3 rounded-[var(--hp-radius-lg)] border border-[var(--hp-border)] bg-[var(--hp-bg-elevated)] p-5">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}
