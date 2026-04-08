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


class SynthesizeRequest(BaseModel):
    output_format: str = "mp4"  # mp4, mxf
    quality: str = "medium"     # ultra, high, medium, low


@router.post("/api/tasks/{task_id}/synthesize")
async def synthesize_video(
    task_id: int,
    body: SynthesizeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Burn subtitles into the video and save the output."""
    import subprocess
    task = await _get_user_task(task_id, user, db)
    if not task.subtitle_path or not os.path.exists(task.subtitle_path):
        raise HTTPException(status_code=404, detail="No subtitle data — run transcription first")
    if not task.video_path or not os.path.exists(task.video_path):
        raise HTTPException(status_code=404, detail="Source video not found")

    base_name = os.path.splitext(os.path.basename(task.video_path))[0]
    out_dir = os.path.dirname(task.video_path)
    fmt = body.output_format.lower()

    quality_crf = {"ultra": "18", "high": "23", "medium": "28", "low": "32"}.get(body.quality, "28")
    out_path = os.path.join(out_dir, f"{base_name}_captioned.{fmt}")

    # Build FFmpeg command — hard-burn the SRT subtitles
    subtitle_filter = f"subtitles={task.subtitle_path.replace(':', r'\\:')}"
    if fmt == "mp4":
        cmd = [
            "ffmpeg", "-y", "-i", task.video_path,
            "-vf", subtitle_filter,
            "-c:v", "libx264", "-crf", quality_crf, "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k",
            out_path,
        ]
    elif fmt == "mxf":
        cmd = [
            "ffmpeg", "-y", "-i", task.video_path,
            "-vf", subtitle_filter,
            "-c:v", "dnxhd", "-b:v", "120M",
            "-c:a", "pcm_s16le",
            out_path,
        ]
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=1800)
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"FFmpeg failed: {result.stderr.decode()[-500:]}"
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Synthesis timed out (30 min limit)")

    # Update task output path
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession as AS
    from app.database import async_session
    async with async_session() as sess:
        from app.models.task import Task as TaskModel
        result_db = await sess.execute(select(TaskModel).where(TaskModel.id == task_id))
        t = result_db.scalar_one_or_none()
        if t:
            t.output_path = out_path
            t.status = "completed"
            await sess.commit()

    return {"output_path": out_path, "detail": "Synthesis complete"}


class TranslateSegmentRequest(BaseModel):
    text: str


@router.post("/api/tasks/{task_id}/translate-segment")
async def translate_segment(
    task_id: int,
    body: TranslateSegmentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Translate a single subtitle segment on demand using the configured LLM."""
    await _get_user_task(task_id, user, db)  # auth check

    from app.config import settings as app_settings
    import openai

    client = openai.OpenAI(
        api_key=app_settings.llm_api_key,
        base_url=app_settings.llm_api_base,
    )
    try:
        resp = client.chat.completions.create(
            model=app_settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional subtitle translator specialising in Traditional Chinese (繁體中文) "
                        "used in Hong Kong and Taiwan. Translate the given English subtitle text to Traditional Chinese. "
                        "Rules: 1. Traditional Chinese ONLY — no simplified. "
                        "2. Return ONLY the translated text. "
                        "3. Keep proper nouns (names, brands) in English when no standard Chinese equivalent exists. "
                        "4. Be concise — match subtitle length."
                    ),
                },
                {"role": "user", "content": body.text},
            ],
            temperature=0.3,
        )
        translation = resp.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

    return {"translated_text": translation}
