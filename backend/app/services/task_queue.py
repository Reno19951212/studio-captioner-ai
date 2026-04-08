"""FIFO task queue manager."""

import asyncio
from collections import deque
from typing import Optional


class TaskQueue:
    def __init__(self):
        self._queue: deque[int] = deque()
        self._event = asyncio.Event()
        self.current_task_id: Optional[int] = None

    @property
    def length(self) -> int:
        return len(self._queue)

    async def enqueue(self, task_id: int) -> None:
        self._queue.append(task_id)
        self._event.set()

    async def dequeue(self) -> int:
        while not self._queue:
            self._event.clear()
            await self._event.wait()
        return self._queue.popleft()

    def cancel(self, task_id: int) -> bool:
        try:
            self._queue.remove(task_id)
            return True
        except ValueError:
            return False
