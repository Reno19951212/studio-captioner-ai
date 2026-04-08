"""Subtitle API routes — get, save, export."""

import os
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.task import Task
from app.models.user import User

router = APIRouter(tags=["subtitles"])

_SRT_TIME = re.compile(
    r"(\d{2}):(\d{2}):(\d{1,2})[.,](\d{3})\s-->\s(\d{2}):(\d{2}):(\d{1,2})[.,](\d{3})"
)


def _ms(h, m, s, ms):
    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)


def _parse_bilingual_srt(path: str) -> List["SubtitleSegment"]:
    """Parse SRT file — automatically separates bilingual subtitles.

    If a block has 2 text lines, treats line 1 as source (EN) and line 2
    as translation (ZH). Never uses language detection.
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()

    segments = []
    for block in re.split(r"\n\s*\n", content.strip()):
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        m = _SRT_TIME.match(lines[1])
        if not m:
            continue
        start = _ms(m.group(1), m.group(2), m.group(3), m.group(4))
        end = _ms(m.group(5), m.group(6), m.group(7), m.group(8))
        text_lines = [l.strip() for l in lines[2:] if l.strip()]
        if not text_lines:
            continue
        source = text_lines[0]
        translation = text_lines[1] if len(text_lines) >= 2 else None
        segments.append(SubtitleSegment(
            text=source,
            start_time=start,
            end_time=end,
            translated_text=translation,
        ))
    return segments


class SubtitleSegment(BaseModel):
    text: str
    start_time: int
    end_time: int
    translated_text: Optional[str] = None


class SubtitleData(BaseModel):
    segments: List[SubtitleSegment]


class SubtitleSaveRequest(BaseModel):
    segments: List[SubtitleSegment]


class ExportRequest(BaseModel):
    format: str = "srt"


async def _get_user_task(task_id: int, user: User, db: AsyncSession) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/api/tasks/{task_id}/subtitles", response_model=SubtitleData)
async def get_subtitles(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_task(task_id, user, db)
    if not task.subtitle_path or not os.path.exists(task.subtitle_path):
        raise HTTPException(status_code=404, detail="No subtitle data available")

    segments = _parse_bilingual_srt(task.subtitle_path)
    return SubtitleData(segments=segments)


@router.put("/api/tasks/{task_id}/subtitles")
async def save_subtitles(
    task_id: int,
    body: SubtitleSaveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_task(task_id, user, db)
    if not task.subtitle_path:
        raise HTTPException(status_code=400, detail="No subtitle path set for this task")

    from core.asr.asr_data import ASRData, ASRDataSeg

    segments = [
        ASRDataSeg(
            text=seg.text,
            start_time=seg.start_time,
            end_time=seg.end_time,
            translated_text=seg.translated_text or "",
        )
        for seg in body.segments
    ]
    asr_data = ASRData(segments)
    asr_data.to_srt(save_path=task.subtitle_path)
    return {"detail": "Subtitles saved"}


@router.post("/api/tasks/{task_id}/export")
async def export_subtitles(
    task_id: int,
    body: ExportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_task(task_id, user, db)
    if not task.subtitle_path or not os.path.exists(task.subtitle_path):
        raise HTTPException(status_code=404, detail="No subtitle data available")

    from core.asr.asr_data import ASRData

    asr_data = ASRData.from_subtitle_file(task.subtitle_path)
    export_dir = os.path.dirname(task.subtitle_path)
    base_name = os.path.splitext(os.path.basename(task.subtitle_path))[0]

    fmt = body.format.lower()
    if fmt == "srt":
        out_path = os.path.join(export_dir, f"{base_name}.srt")
        asr_data.to_srt(save_path=out_path)
    elif fmt == "ass":
        out_path = os.path.join(export_dir, f"{base_name}.ass")
        asr_data.to_ass(save_path=out_path)
    elif fmt == "vtt":
        out_path = os.path.join(export_dir, f"{base_name}.vtt")
        asr_data.to_vtt(save_path=out_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    return FileResponse(out_path, filename=os.path.basename(out_path))
