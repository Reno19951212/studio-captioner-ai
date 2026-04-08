"""Settings schemas."""

from typing import List
from pydantic import BaseModel


class SettingsResponse(BaseModel):
    storage_base_path: str
    default_asr_model: str
    default_whisper_model: str
    llm_api_base: str
    llm_model: str


class SettingsUpdate(BaseModel):
    storage_base_path: str | None = None
    default_asr_model: str | None = None
    default_whisper_model: str | None = None
    llm_api_base: str | None = None
    llm_model: str | None = None


class AvailableModels(BaseModel):
    asr_models: List[str]
    whisper_sizes: List[str]
