"""Settings API routes."""

from fastapi import APIRouter, Depends

from app.config import settings
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.settings import AvailableModels, SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(user: User = Depends(get_current_user)):
    return SettingsResponse(
        storage_base_path=settings.storage_base_path,
        default_asr_model=settings.default_asr_model,
        default_whisper_model=settings.default_whisper_model,
        llm_api_base=settings.llm_api_base,
        llm_model=settings.llm_model,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(body: SettingsUpdate, user: User = Depends(get_current_user)):
    if body.storage_base_path is not None:
        settings.storage_base_path = body.storage_base_path
    if body.default_asr_model is not None:
        settings.default_asr_model = body.default_asr_model
    if body.default_whisper_model is not None:
        settings.default_whisper_model = body.default_whisper_model
    if body.llm_api_base is not None:
        settings.llm_api_base = body.llm_api_base
    if body.llm_model is not None:
        settings.llm_model = body.llm_model
    return SettingsResponse(
        storage_base_path=settings.storage_base_path,
        default_asr_model=settings.default_asr_model,
        default_whisper_model=settings.default_whisper_model,
        llm_api_base=settings.llm_api_base,
        llm_model=settings.llm_model,
    )


@router.get("/models", response_model=AvailableModels)
async def get_available_models(user: User = Depends(get_current_user)):
    import os
    from pathlib import Path
    from core.config import MODEL_PATH

    # Detect downloaded whisper models by scanning model files
    all_sizes = ["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3"]
    available = []
    for size in all_sizes:
        matches = list(Path(MODEL_PATH).glob(f"*ggml*{size}*"))
        if matches:
            available.append(size)

    return AvailableModels(
        asr_models=["whisper_cpp"],
        whisper_sizes=available if available else ["base"],
    )


@router.get("/validate-path")
async def validate_path(path: str, user: User = Depends(get_current_user)):
    """Check whether a file path exists on the server."""
    import os
    exists = os.path.isfile(path)
    readable = os.access(path, os.R_OK) if exists else False
    return {"exists": exists, "readable": readable, "path": path}
