"""WebSocket handlers for real-time progress and queue updates."""

import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ProgressManager:
    def __init__(self):
        self._task_subscribers: Dict[int, Set[WebSocket]] = {}
        self._queue_subscribers: Set[WebSocket] = set()

    def subscribe(self, task_id: int, ws: WebSocket):
        if task_id not in self._task_subscribers:
            self._task_subscribers[task_id] = set()
        self._task_subscribers[task_id].add(ws)

    def unsubscribe(self, task_id: int, ws: WebSocket):
        if task_id in self._task_subscribers:
            self._task_subscribers[task_id].discard(ws)
            if not self._task_subscribers[task_id]:
                del self._task_subscribers[task_id]

    def subscribe_queue(self, ws: WebSocket):
        self._queue_subscribers.add(ws)

    def unsubscribe_queue(self, ws: WebSocket):
        self._queue_subscribers.discard(ws)

    async def broadcast_task(self, task_id: int, data: dict):
        message = json.dumps(data)
        subscribers = self._task_subscribers.get(task_id, set()).copy()
        for ws in subscribers:
            try:
                await ws.send_text(message)
            except Exception:
                self._task_subscribers.get(task_id, set()).discard(ws)

    async def broadcast_queue(self, data: dict):
        message = json.dumps(data)
        for ws in self._queue_subscribers.copy():
            try:
                await ws.send_text(message)
            except Exception:
                self._queue_subscribers.discard(ws)


progress_manager = ProgressManager()


@router.websocket("/ws/tasks/{task_id}")
async def ws_task_progress(websocket: WebSocket, task_id: int):
    await websocket.accept()
    progress_manager.subscribe(task_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        progress_manager.unsubscribe(task_id, websocket)


@router.websocket("/ws/queue")
async def ws_queue_status(websocket: WebSocket):
    await websocket.accept()
    progress_manager.subscribe_queue(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        progress_manager.unsubscribe_queue(websocket)
