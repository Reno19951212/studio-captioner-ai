"""Task request/response schemas."""

import datetime
from typing import Optional

from pydantic import BaseModel


class TaskCreate(BaseModel):
    video_path: str
    asr_model: str = "whisper_cpp"
    whisper_model: str = "base"
    config: dict = {}


class TaskResponse(BaseModel):
    id: int
    user_id: int
    status: str
    video_path: str
    output_path: Optional[str] = None
    subtitle_path: Optional[str] = None
    progress: int = 0
    stage: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None


class QueueStatus(BaseModel):
    queue_length: int
    current_task: Optional[TaskResponse] = None
