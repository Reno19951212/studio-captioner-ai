interface ProgressBarProps { progress: number; stage: string | null; }

const STAGE_LABELS: Record<string, { label: string; color: string }> = {
  transcribe: { label: "Transcribing…", color: "#60a5fa" },
  translate:  { label: "Translating…",  color: "#a78bfa" },
  optimize:   { label: "Optimizing…",   color: "#34d399" },
  split:      { label: "Splitting…",    color: "#fbbf24" },
  done:       { label: "Done",          color: "#34d399" },
};

export function ProgressBar({ progress, stage }: ProgressBarProps) {
  const info = stage ? STAGE_LABELS[stage] : null;
  const label = info?.label ?? stage ?? "Processing…";
  const color = info?.color ?? "#34d399";

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span style={{ color }}>{label}</span>
        <span style={{ color }}>{progress}%</span>
      </div>
      <div className="bg-zinc-800 rounded-full h-1.5">
        <div
          className="h-1.5 rounded-full transition-all duration-500"
          style={{ width: `${progress}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
