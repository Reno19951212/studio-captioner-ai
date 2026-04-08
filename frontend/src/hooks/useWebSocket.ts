import { useEffect, useRef, useCallback } from "react";
import { connectQueueWs, connectTaskWs } from "../services/ws";
import { useTaskStore } from "../store/taskStore";
import type { QueueStatus, Task } from "../types/task";

/** Queue WebSocket with auto-reconnect + full task status updates. */
export function useQueueWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const delay = useRef(1000);
  const unmounted = useRef(false);

  const { updateQueueFromWs, updateTaskFromWs, fetchTasks } = useTaskStore();

  const connect = useCallback(() => {
    if (unmounted.current) return;

    const ws = connectQueueWs((data) => {
      const d = data as Record<string, unknown>;

      // Queue-level update from backend broadcast
      if (d.type === "task_update" && d.task) {
        const t = d.task as { task_id: number; stage: string; progress: number; status: string };
        // Update the task's status + stage + progress in the store
        updateTaskFromWs(t.task_id, {
          stage: t.stage,
          progress: t.progress,
          status: t.status as Task["status"],
        } as Partial<Task>);

        // When a task completes or fails, re-fetch full list so Dashboard is accurate
        if (t.status === "ready_for_review" || t.status === "completed" || t.status === "failed") {
          fetchTasks();
        }
      }

      // Legacy queue status message
      if ("queue_length" in d && !("type" in d)) {
        updateQueueFromWs(d as unknown as QueueStatus);
      }

      // Also update queue count
      if ("queue_length" in d && "current_task" in d) {
        updateQueueFromWs({
          queue_length: d.queue_length as number,
          current_task: d.current_task as Task | null,
        });
      }
    });

    ws.onopen = () => { delay.current = 1000; };
    ws.onclose = () => {
      if (unmounted.current) return;
      retryRef.current = setTimeout(() => {
        delay.current = Math.min(delay.current * 2, 30000);
        connect();
      }, delay.current);
    };

    wsRef.current = ws;
  }, [updateQueueFromWs, updateTaskFromWs, fetchTasks]);

  useEffect(() => {
    unmounted.current = false;
    connect();
    return () => {
      unmounted.current = true;
      if (retryRef.current) clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return wsRef;
}

/** Task-specific WebSocket with full status updates. */
export function useTaskWebSocket(taskId: number) {
  const { updateTaskFromWs, fetchTasks } = useTaskStore();

  useEffect(() => {
    const ws = connectTaskWs(taskId, (data) => {
      const d = data as Record<string, unknown>;
      if ("stage" in d && "progress" in d) {
        updateTaskFromWs(taskId, {
          stage: d.stage as string,
          progress: d.progress as number,
          status: (d.status ?? "processing") as Task["status"],
        } as Partial<Task>);

        if (d.status === "ready_for_review" || d.status === "completed" || d.status === "failed") {
          fetchTasks();
        }
      }
    });
    return () => ws.close();
  }, [taskId, updateTaskFromWs, fetchTasks]);
}
