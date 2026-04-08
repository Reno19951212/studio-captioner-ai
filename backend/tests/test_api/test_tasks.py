import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.database import Base, async_engine
from app.main import create_app


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
async def auth_headers(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "pass123"})
    resp = await client.post("/api/auth/login", json={"name": "alice", "password": "pass123"})
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_task(client, auth_headers):
    resp = await client.post(
        "/api/tasks",
        json={"video_path": "/shared/input/interview.mxf", "asr_model": "faster_whisper"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["video_path"] == "/shared/input/interview.mxf"
    assert data["status"] == "queued"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_tasks(client, auth_headers):
    await client.post("/api/tasks", json={"video_path": "/shared/input/a.mxf"}, headers=auth_headers)
    await client.post("/api/tasks", json={"video_path": "/shared/input/b.mxf"}, headers=auth_headers)
    resp = await client.get("/api/tasks", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_get_task(client, auth_headers):
    create_resp = await client.post("/api/tasks", json={"video_path": "/shared/input/a.mxf"}, headers=auth_headers)
    task_id = create_resp.json()["id"]
    resp = await client.get(f"/api/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


@pytest.mark.asyncio
async def test_delete_queued_task(client, auth_headers):
    create_resp = await client.post("/api/tasks", json={"video_path": "/shared/input/a.mxf"}, headers=auth_headers)
    task_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 200
    get_resp = await client.get(f"/api/tasks/{task_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_queue_status(client, auth_headers):
    resp = await client.get("/api/queue", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "queue_length" in data
    assert "current_task" in data
