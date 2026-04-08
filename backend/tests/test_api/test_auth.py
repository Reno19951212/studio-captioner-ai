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


@pytest.mark.asyncio
async def test_register_user(client):
    resp = await client.post("/api/auth/register", json={"name": "alice", "password": "secret123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "alice"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_name(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "secret123"})
    resp = await client.post("/api/auth/register", json={"name": "alice", "password": "other456"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "secret123"})
    resp = await client.post("/api/auth/login", json={"name": "alice", "password": "secret123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["name"] == "alice"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "secret123"})
    resp = await client.post("/api/auth/login", json={"name": "alice", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    resp = await client.get("/api/tasks")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_protected_endpoint_with_token(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "secret123"})
    login_resp = await client.post("/api/auth/login", json={"name": "alice", "password": "secret123"})
    token = login_resp.json()["token"]
    resp = await client.get("/api/tasks", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
