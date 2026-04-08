const WS_BASE = "ws://localhost:8000";

export function connectTaskWs(
  taskId: number,
  onMessage: (data: Record<string, unknown>) => void
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/ws/tasks/${taskId}`);
  ws.onmessage = (event) => onMessage(JSON.parse(event.data));
  return ws;
}

export function connectQueueWs(
  onMessage: (data: Record<string, unknown>) => void
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/ws/queue`);
  ws.onmessage = (event) => onMessage(JSON.parse(event.data));
  return ws;
}
