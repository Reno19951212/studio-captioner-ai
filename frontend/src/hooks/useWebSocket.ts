import { useEffect, useRef } from "react";
import { connectQueueWs } from "../services/ws";
import { useTaskStore } from "../store/taskStore";
import type { QueueStatus } from "../types/task";

export function useQueueWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const updateQueueFromWs = useTaskStore((s) => s.updateQueueFromWs);
  useEffect(() => {
    const ws = connectQueueWs((data) => { updateQueueFromWs(data as unknown as QueueStatus); });
    wsRef.current = ws;
    return () => ws.close();
  }, [updateQueueFromWs]);
  return wsRef;
}
