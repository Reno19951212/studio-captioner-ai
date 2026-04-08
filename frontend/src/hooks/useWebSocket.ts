import { useEffect, useRef, useCallback } from "react";
import { connectQueueWs, connectTaskWs } from "../services/ws";
import { useTaskStore } from "../store/taskStore";
import type { QueueStatus, Task } from "../types/task";

/** Queue WebSocket with auto-reconnect (exponential backoff up to 30s). */
export function useQueueWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const delay = useRef(1000);
  const unmounted = useRef(false);

  const updateQueueFromWs = useTaskStore((s) => s.updateQueueFromWs);
  const updateTaskFromWs = useTaskStore((s) => s.updateTaskFromWs);

  const connect = useCallback(() => {
    if (unmounted.current) return;

    const ws = connectQueueWs((data) => {
      // Queue status update
      if ("queue_length" in data) {
        updateQueueFromWs(data as unknown as QueueStatus);
      }
      // Task progress update
      if ("task_id" in data) {
        const { task_id, stage, progress } = data as { task_id: number; stage: string; progress: number };
        updateTaskFromWs(task_id, { stage, progress } as Partial<Task>);
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
  }, [updateQueueFromWs, updateTaskFromWs]);

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

/** Task-specific WebSocket — subscribes to a single task's progress. */
export function useTaskWebSocket(taskId: number) {
  const updateTaskFromWs = useTaskStore((s) => s.updateTaskFromWs);

  useEffect(() => {
    const ws = connectTaskWs(taskId, (data) => {
      if ("stage" in data && "progress" in data) {
        updateTaskFromWs(taskId, {
          stage: data.stage as string,
          progress: data.progress as number,
        } as Partial<Task>);
      }
    });
    return () => ws.close();
  }, [taskId, updateTaskFromWs]);
}
