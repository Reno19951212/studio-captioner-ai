"""FastAPI application factory."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, tasks, subtitles, preview
from app.api import settings as settings_api
from app.database import Base, async_engine
from app.services.task_queue import TaskQueue
from app.ws import handlers as ws_handlers
from features.glossary import api as glossary_api

task_queue = TaskQueue()


async def queue_worker():
    from app.services.pipeline import run_pipeline
    from app.ws.handlers import progress_manager

    async def progress_callback(task_id: int, stage: str, progress: int, detail: str):
        """Broadcast pipeline progress to WebSocket subscribers."""
        # Determine status from stage
        if stage == "done":
            status = "ready_for_review"
        elif stage == "failed":
            status = "failed"
        else:
            status = "processing"

        task_msg = {
            "task_id": task_id,
            "stage": stage,
            "progress": progress,
            "detail": detail,
            "status": status,
        }
        # Broadcast to task-specific subscribers
        await progress_manager.broadcast_task(task_id, task_msg)
        # Broadcast to queue-wide subscribers (Dashboard)
        await progress_manager.broadcast_queue({
            "type": "task_update",
            "queue_length": task_queue.length,
            "task": task_msg,
            "current_task": {
                "id": task_id, "stage": stage, "progress": progress,
            } if task_queue.current_task_id else None,
        })

    while True:
        task_id = await task_queue.dequeue()
        task_queue.current_task_id = task_id
        try:
            await run_pipeline(task_id, progress_callback=progress_callback)
        except Exception:
            pass
        finally:
            task_queue.current_task_id = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    worker_task = asyncio.create_task(queue_worker())
    app.state.task_queue = task_queue
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    app = FastAPI(title="Studio Captioner AI", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(tasks.router)
    app.include_router(subtitles.router)
    app.include_router(preview.router)
    app.include_router(settings_api.router)
    app.include_router(ws_handlers.router)
    app.include_router(glossary_api.router)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app
