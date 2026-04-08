import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTaskStore } from "../store/taskStore";
import { useQueueWebSocket } from "../hooks/useWebSocket";
import { QueueList } from "../components/queue/QueueList";
import type { Task } from "../types/task";

export function Dashboard() {
  const { tasks, fetchTasks, fetchQueue } = useTaskStore();
  const navigate = useNavigate();
  useQueueWebSocket();

  useEffect(() => { fetchTasks(); fetchQueue(); }, [fetchTasks, fetchQueue]);

  const queued = tasks.filter((t) => t.status === "queued");
  const processing = tasks.filter((t) => t.status === "processing");
  const review = tasks.filter((t) => t.status === "ready_for_review");
  const completed = tasks.filter((t) => t.status === "completed");

  const handleTaskClick = (task: Task) => {
    if (task.status === "ready_for_review" || task.status === "completed") {
      navigate(`/editor/${task.id}`);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-emerald-500/10 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-emerald-400">{processing.length}</div>
          <div className="text-xs text-zinc-500 mt-1">Processing</div>
        </div>
        <div className="bg-amber-500/10 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-amber-400">{queued.length}</div>
          <div className="text-xs text-zinc-500 mt-1">In Queue</div>
        </div>
        <div className="bg-pink-500/10 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-pink-400">{review.length}</div>
          <div className="text-xs text-zinc-500 mt-1">Needs Review</div>
        </div>
        <div className="bg-blue-500/10 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-blue-400">{completed.length}</div>
          <div className="text-xs text-zinc-500 mt-1">Completed</div>
        </div>
      </div>
      {processing.length > 0 && <section className="mb-6"><h2 className="text-sm font-medium text-zinc-400 mb-2">Processing</h2><QueueList tasks={processing} /></section>}
      {queued.length > 0 && <section className="mb-6"><h2 className="text-sm font-medium text-zinc-400 mb-2">Queue</h2><QueueList tasks={queued} /></section>}
      {review.length > 0 && <section><h2 className="text-sm font-medium text-zinc-400 mb-2">Needs Review</h2><QueueList tasks={review} onTaskClick={handleTaskClick} /></section>}
    </div>
  );
}
