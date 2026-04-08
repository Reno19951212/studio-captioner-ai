"""Preview API — video streaming, waveform data, thumbnails."""

import json
import os
import struct
import subprocess
import tempfile

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.task import Task
from app.models.user import User

router = APIRouter(prefix="/api/preview", tags=["preview"])


async def _get_user_task(task_id: int, user: User, db: AsyncSession) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{task_id}/video")
async def preview_video(
    task_id: int, request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_task(task_id, user, db)
    if not task.video_path or not os.path.exists(task.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    file_size = os.path.getsize(task.video_path)
    range_header = request.headers.get("range")

    if range_header:
        range_val = range_header.replace("bytes=", "")
        start_str, end_str = range_val.split("-")
        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1
        chunk_size = end - start + 1

        def iter_file():
            with open(task.video_path, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    read_size = min(8192, remaining)
                    data = f.read(read_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        return StreamingResponse(
            iter_file(), status_code=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Type": "video/mp4",
            },
        )

    return FileResponse(task.video_path, media_type="video/mp4")


@router.get("/{task_id}/waveform")
async def get_waveform(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_task(task_id, user, db)
    if not task.video_path or not os.path.exists(task.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    waveform_path = task.video_path + ".peaks.json"
    if os.path.exists(waveform_path):
        return FileResponse(waveform_path, media_type="application/json")

    try:
        raw_path = os.path.join(tempfile.gettempdir(), f"task_{task_id}_raw.pcm")
        subprocess.run(
            ["ffmpeg", "-y", "-i", task.video_path, "-ac", "1", "-ar", "8000", "-f", "s16le", raw_path],
            capture_output=True, timeout=120,
        )
        if not os.path.exists(raw_path):
            raise HTTPException(status_code=500, detail="Failed to extract audio")

        peaks = []
        with open(raw_path, "rb") as f:
            while True:
                chunk = f.read(8000 * 2)
                if not chunk:
                    break
                samples = struct.unpack(f"<{len(chunk)//2}h", chunk)
                peak = max(abs(s) for s in samples) / 32768.0 if samples else 0
                peaks.append(round(peak, 3))
        os.unlink(raw_path)

        with open(waveform_path, "w") as f:
            json.dump({"peaks": peaks, "sample_rate": 1}, f)
        return FileResponse(waveform_path, media_type="application/json")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Waveform generation timed out")


@router.get("/{task_id}/thumbnail")
async def get_thumbnail(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_task(task_id, user, db)
    if not task.video_path or not os.path.exists(task.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    thumb_path = task.video_path + ".thumb.jpg"
    if os.path.exists(thumb_path):
        return FileResponse(thumb_path, media_type="image/jpeg")

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", task.video_path, "-ss", "00:00:02", "-frames:v", "1", "-q:v", "5", thumb_path],
            capture_output=True, timeout=30,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate thumbnail")

    if not os.path.exists(thumb_path):
        raise HTTPException(status_code=500, detail="Thumbnail generation failed")
    return FileResponse(thumb_path, media_type="image/jpeg")
