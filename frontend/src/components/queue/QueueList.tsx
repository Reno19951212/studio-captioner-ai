import type { Task } from "../../types/task";
import { ProgressBar } from "./ProgressBar";

interface QueueListProps { tasks: Task[]; onTaskClick?: (task: Task) => void; }

const statusColor: Record<string, string> = {
  queued: "text-amber-400", processing: "text-emerald-400", ready_for_review: "text-pink-400",
  completed: "text-blue-400", failed: "text-red-400",
};

export function QueueList({ tasks, onTaskClick }: QueueListProps) {
  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <div key={task.id} onClick={() => onTaskClick?.(task)}
          className="bg-zinc-900 rounded-lg p-3 cursor-pointer hover:bg-zinc-800/80 transition">
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-zinc-200 truncate max-w-xs">{task.video_path.split("/").pop()}</span>
            <span className={`text-xs ${statusColor[task.status] || "text-zinc-500"}`}>{task.status.replace(/_/g, " ")}</span>
          </div>
          {task.status === "processing" && <ProgressBar progress={task.progress} stage={task.stage} />}
        </div>
      ))}
      {tasks.length === 0 && <p className="text-zinc-600 text-sm">No tasks</p>}
    </div>
  );
}
