"""Pipeline orchestrator — connects API layer to core engine."""

import datetime
import json
import os
import tempfile
import traceback
from typing import Callable, Optional

from sqlalchemy import select

from app.database import async_session
from app.models.task import Task


async def update_task_status(
    task_id: int,
    status: str,
    stage: Optional[str] = None,
    progress: int = 0,
    error_message: Optional[str] = None,
    output_path: Optional[str] = None,
    subtitle_path: Optional[str] = None,
):
    async with async_session() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            return
        task.status = status
        if stage is not None:
            task.stage = stage
        task.progress = progress
        if error_message is not None:
            task.error_message = error_message
        if output_path is not None:
            task.output_path = output_path
        if subtitle_path is not None:
            task.subtitle_path = subtitle_path
        if status in ("completed", "ready_for_review", "failed"):
            task.completed_at = datetime.datetime.now(datetime.timezone.utc)
        await db.commit()


async def run_pipeline(task_id: int, progress_callback: Optional[Callable] = None):
    """Execute the full captioning pipeline for a task."""
    async with async_session() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            return
        config = json.loads(task.config_json) if task.config_json else {}
        video_path = task.video_path

    try:
        await update_task_status(task_id, "processing", stage="transcribe", progress=0)
        if progress_callback:
            await progress_callback(task_id, "transcribe", 0, "Starting transcription")

        from core.asr.transcribe import transcribe
        from core.entities import TranscribeConfig, TranscribeModelEnum
        from core.utils.video_utils import video2audio

        audio_path = os.path.join(tempfile.gettempdir(), f"task_{task_id}.wav")
        video2audio(video_path, audio_path)

        asr_model = config.get("asr_model", "faster_whisper")
        model_enum = (
            TranscribeModelEnum.FASTER_WHISPER
            if asr_model == "faster_whisper"
            else TranscribeModelEnum.WHISPER_CPP
        )
        transcribe_config = TranscribeConfig(transcribe_model=model_enum)

        asr_data = transcribe(audio_path, transcribe_config)

        subtitle_dir = os.path.dirname(video_path)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        subtitle_path = os.path.join(subtitle_dir, f"{base_name}.srt")
        asr_data.to_srt(subtitle_path)

        await update_task_status(
            task_id, "ready_for_review", stage="done", progress=100, subtitle_path=subtitle_path,
        )
        if progress_callback:
            await progress_callback(task_id, "done", 100, "Ready for review")

    except Exception as e:
        await update_task_status(
            task_id, "failed", error_message=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
        )
        if progress_callback:
            await progress_callback(task_id, "failed", 0, str(e))
