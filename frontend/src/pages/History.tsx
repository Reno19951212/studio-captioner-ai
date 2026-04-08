import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTaskStore } from "../store/taskStore";
import { QueueList } from "../components/queue/QueueList";
import type { Task } from "../types/task";

export function History() {
  const { tasks, fetchTasks } = useTaskStore();
  const navigate = useNavigate();
  useEffect(() => { fetchTasks(); }, [fetchTasks]);
  const sorted = [...tasks].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  const handleTaskClick = (task: Task) => {
    if (task.status === "ready_for_review" || task.status === "completed") {
      navigate(`/editor/${task.id}`);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">History</h1>
      {sorted.length === 0 ? (
        <p className="text-zinc-600 text-sm">No tasks yet.</p>
      ) : (
        <QueueList tasks={sorted} onTaskClick={handleTaskClick} />
      )}
    </div>
  );
}
