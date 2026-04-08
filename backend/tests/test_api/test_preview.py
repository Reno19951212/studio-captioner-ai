import os
import tempfile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.database import Base, async_engine, async_session
from app.main import create_app
from app.models.task import Task
from app.models.user import User
from app.services.auth import hash_password


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_and_task_with_video(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "pass123"})
    resp = await client.post("/api/auth/login", json={"name": "alice", "password": "pass123"})
    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    tmpdir = tempfile.mkdtemp()
    video_path = os.path.join(tmpdir, "test.mp4")
    with open(video_path, "wb") as f:
        f.write(b"\x00" * 1024)

    async with async_session() as db:
        result = await db.execute(select(User).where(User.name == "alice"))
        user = result.scalar_one()
        task = Task(user_id=user.id, video_path=video_path, status="ready_for_review")
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return headers, task.id


@pytest.mark.asyncio
async def test_preview_video_streaming(client, auth_and_task_with_video):
    headers, task_id = auth_and_task_with_video
    resp = await client.get(f"/api/preview/{task_id}/video", headers=headers)
    assert resp.status_code == 200
    assert len(resp.content) == 1024


@pytest.mark.asyncio
async def test_preview_video_not_found(client, auth_and_task_with_video):
    headers, _ = auth_and_task_with_video
    async with async_session() as db:
        result = await db.execute(select(User).where(User.name == "alice"))
        user = result.scalar_one()
        task = Task(user_id=user.id, video_path="/nonexistent/video.mp4", status="queued")
        db.add(task)
        await db.commit()
        await db.refresh(task)
        bad_task_id = task.id
    resp = await client.get(f"/api/preview/{bad_task_id}/video", headers=headers)
    assert resp.status_code == 404
