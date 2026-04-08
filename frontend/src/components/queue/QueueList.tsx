import type { Task } from "../../types/task";
import { ProgressBar } from "./ProgressBar";
import { useTaskStore } from "../../store/taskStore";

interface QueueListProps {
  tasks: Task[];
  onTaskClick?: (task: Task) => void;
}

const statusColor: Record<string, string> = {
  queued: "text-amber-400",
  processing: "text-emerald-400",
  ready_for_review: "text-pink-400",
  completed: "text-blue-400",
  failed: "text-red-400",
};

const statusLabel: Record<string, string> = {
  queued: "Queued",
  processing: "Processing",
  ready_for_review: "Ready for Review",
  completed: "Completed",
  failed: "Failed",
};

export function QueueList({ tasks, onTaskClick }: QueueListProps) {
  const { deleteTask } = useTaskStore();

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <div
          key={task.id}
          onClick={() => onTaskClick?.(task)}
          className={`bg-zinc-900 rounded-lg p-3 transition ${
            onTaskClick && (task.status === "ready_for_review" || task.status === "completed")
              ? "cursor-pointer hover:bg-zinc-800/80"
              : "cursor-default"
          }`}
        >
          <div className="flex justify-between items-start gap-2">
            <div className="flex-1 min-w-0">
              <div className="text-sm text-zinc-200 truncate">
                {task.video_path.split("/").pop()}
              </div>
              <div className="text-xs text-zinc-600 mt-0.5">
                {new Date(task.created_at).toLocaleString()}
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <span className={`text-xs ${statusColor[task.status] || "text-zinc-500"}`}>
                {statusLabel[task.status] || task.status}
              </span>
              {task.status === "queued" && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteTask(task.id).catch(() => {});
                  }}
                  className="text-zinc-600 hover:text-red-400 text-xs px-1"
                  title="Cancel task"
                >
                  ✕
                </button>
              )}
            </div>
          </div>
          {task.status === "processing" && (
            <div className="mt-2">
              <ProgressBar progress={task.progress} stage={task.stage} />
            </div>
          )}
          {task.status === "failed" && task.error_message && (
            <div className="mt-1 text-xs text-red-400 truncate">
              {task.error_message.split("\n")[0]}
            </div>
          )}
        </div>
      ))}
      {tasks.length === 0 && <p className="text-zinc-600 text-sm">No tasks</p>}
    </div>
  );
}
