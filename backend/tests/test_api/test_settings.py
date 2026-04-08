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
    await client.post("/api/auth/register", json={"name": "admin", "password": "pass123"})
    resp = await client.post("/api/auth/login", json={"name": "admin", "password": "pass123"})
    return {"Authorization": f"Bearer {resp.json()['token']}"}


@pytest.mark.asyncio
async def test_get_settings(client, auth_headers):
    resp = await client.get("/api/settings", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "default_asr_model" in data
    assert "llm_model" in data
    assert "storage_base_path" in data


@pytest.mark.asyncio
async def test_get_available_models(client, auth_headers):
    resp = await client.get("/api/settings/models", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "asr_models" in data
    assert "faster_whisper" in data["asr_models"]
    assert "whisper_cpp" in data["asr_models"]
