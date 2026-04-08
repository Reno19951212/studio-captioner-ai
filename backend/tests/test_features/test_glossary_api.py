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
    return {"Authorization": f"Bearer {resp.json()['token']}"}

@pytest.mark.asyncio
async def test_create_glossary(client, auth_headers):
    resp = await client.post("/api/glossaries", json={"name": "News Terms", "description": "For news"}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "News Terms"

@pytest.mark.asyncio
async def test_list_glossaries(client, auth_headers):
    await client.post("/api/glossaries", json={"name": "A"}, headers=auth_headers)
    await client.post("/api/glossaries", json={"name": "B"}, headers=auth_headers)
    resp = await client.get("/api/glossaries", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2

@pytest.mark.asyncio
async def test_add_entries(client, auth_headers):
    create_resp = await client.post("/api/glossaries", json={"name": "Test"}, headers=auth_headers)
    gid = create_resp.json()["id"]
    resp = await client.post(f"/api/glossaries/{gid}/entries", json={"entries": [{"source_term": "Fed", "target_term": "聯儲局"}, {"source_term": "APAC", "target_term": "亞太區"}]}, headers=auth_headers)
    assert resp.status_code == 201
    assert len(resp.json()) == 2

@pytest.mark.asyncio
async def test_get_entries(client, auth_headers):
    create_resp = await client.post("/api/glossaries", json={"name": "Test"}, headers=auth_headers)
    gid = create_resp.json()["id"]
    await client.post(f"/api/glossaries/{gid}/entries", json={"entries": [{"source_term": "Fed", "target_term": "聯儲局"}]}, headers=auth_headers)
    resp = await client.get(f"/api/glossaries/{gid}/entries", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

@pytest.mark.asyncio
async def test_delete_glossary(client, auth_headers):
    create_resp = await client.post("/api/glossaries", json={"name": "ToDelete"}, headers=auth_headers)
    gid = create_resp.json()["id"]
    resp = await client.delete(f"/api/glossaries/{gid}", headers=auth_headers)
    assert resp.status_code == 200
    list_resp = await client.get("/api/glossaries", headers=auth_headers)
    assert len(list_resp.json()) == 0

@pytest.mark.asyncio
async def test_csv_import(client, auth_headers):
    create_resp = await client.post("/api/glossaries", json={"name": "CSV Test"}, headers=auth_headers)
    gid = create_resp.json()["id"]
    csv_content = "source_term,target_term\nFed,聯儲局\nAPAC,亞太區\n"
    resp = await client.post(f"/api/glossaries/{gid}/import", files={"file": ("terms.csv", csv_content, "text/csv")}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["imported"] == 2

@pytest.mark.asyncio
async def test_csv_export(client, auth_headers):
    create_resp = await client.post("/api/glossaries", json={"name": "Export Test"}, headers=auth_headers)
    gid = create_resp.json()["id"]
    await client.post(f"/api/glossaries/{gid}/entries", json={"entries": [{"source_term": "Fed", "target_term": "聯儲局"}]}, headers=auth_headers)
    resp = await client.get(f"/api/glossaries/{gid}/export", headers=auth_headers)
    assert resp.status_code == 200
    assert "Fed" in resp.text and "聯儲局" in resp.text
