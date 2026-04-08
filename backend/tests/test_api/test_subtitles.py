import os
import tempfile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

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
async def auth_and_task(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "pass123"})
    resp = await client.post("/api/auth/login", json={"name": "alice", "password": "pass123"})
    token = resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    tmpdir = tempfile.mkdtemp()
    srt_path = os.path.join(tmpdir, "test.srt")
    with open(srt_path, "w") as f:
        f.write("1\n00:00:01,000 --> 00:00:03,000\nHello world\n\n")
        f.write("2\n00:00:04,000 --> 00:00:06,000\nSecond line\n\n")

    async with async_session() as db:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.name == "alice"))
        user = result.scalar_one()
        task = Task(user_id=user.id, video_path="/fake/video.mxf", status="ready_for_review", subtitle_path=srt_path)
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return headers, task.id, srt_path


@pytest.mark.asyncio
async def test_get_subtitles(client, auth_and_task):
    headers, task_id, _ = auth_and_task
    resp = await client.get(f"/api/tasks/{task_id}/subtitles", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "segments" in data
    assert len(data["segments"]) == 2
    assert data["segments"][0]["text"] == "Hello world"


@pytest.mark.asyncio
async def test_save_subtitles(client, auth_and_task):
    headers, task_id, _ = auth_and_task
    resp = await client.put(
        f"/api/tasks/{task_id}/subtitles",
        json={"segments": [
            {"text": "Modified hello", "start_time": 1000, "end_time": 3000},
            {"text": "Modified second", "start_time": 4000, "end_time": 6000},
        ]},
        headers=headers,
    )
    assert resp.status_code == 200
    get_resp = await client.get(f"/api/tasks/{task_id}/subtitles", headers=headers)
    assert get_resp.json()["segments"][0]["text"] == "Modified hello"
