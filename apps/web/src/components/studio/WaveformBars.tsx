type WaveformBarsProps = {
  peaks: number[];
  className?: string;
};

export function WaveformBars({ peaks, className = "" }: WaveformBarsProps) {
  if (peaks.length === 0) return null;
  return (
    <div
      className={`flex h-full min-h-[4rem] items-end gap-px rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-bg-subtle)] p-2 ${className}`}
      role="img"
      aria-label="Waveform"
    >
      {peaks.map((peak, i) => (
        <div
          key={i}
          className="flex-1 rounded-sm bg-[var(--hp-accent)]/80"
          style={{ height: `${Math.max(4, peak * 100)}%`, minHeight: 4 }}
        />
      ))}
    </div>
  );
}
