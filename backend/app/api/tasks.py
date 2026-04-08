"""Tasks API routes — stub."""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(tags=["tasks"])


@router.get("/api/tasks")
async def list_tasks(user: User = Depends(get_current_user)):
    return []
