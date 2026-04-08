interface ProgressBarProps { progress: number; stage: string | null; }

export function ProgressBar({ progress, stage }: ProgressBarProps) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-zinc-400">{stage || "Waiting"}</span>
        <span className="text-emerald-400">{progress}%</span>
      </div>
      <div className="bg-zinc-800 rounded-full h-1.5">
        <div className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}
