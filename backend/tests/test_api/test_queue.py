import pytest
import pytest_asyncio

from app.services.task_queue import TaskQueue


@pytest.mark.asyncio
async def test_queue_enqueue_dequeue():
    queue = TaskQueue()
    await queue.enqueue(1)
    await queue.enqueue(2)
    assert queue.length == 2
    task_id = await queue.dequeue()
    assert task_id == 1
    assert queue.length == 1


@pytest.mark.asyncio
async def test_queue_cancel():
    queue = TaskQueue()
    await queue.enqueue(1)
    await queue.enqueue(2)
    await queue.enqueue(3)
    removed = queue.cancel(2)
    assert removed is True
    assert queue.length == 2
    removed_again = queue.cancel(2)
    assert removed_again is False


@pytest.mark.asyncio
async def test_queue_current_task():
    queue = TaskQueue()
    assert queue.current_task_id is None
    await queue.enqueue(42)
    queue.current_task_id = 42
    assert queue.current_task_id == 42
