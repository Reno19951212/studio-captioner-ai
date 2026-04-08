import { useEffect } from "react";
import { useTaskStore } from "../store/taskStore";
import { QueueList } from "../components/queue/QueueList";

export function History() {
  const { tasks, fetchTasks } = useTaskStore();
  useEffect(() => { fetchTasks(); }, [fetchTasks]);
  const sorted = [...tasks].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">History</h1>
      <QueueList tasks={sorted} />
    </div>
  );
}
