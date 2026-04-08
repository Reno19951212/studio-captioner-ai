import pytest
import pytest_asyncio
from app.database import Base, async_engine, async_session
from features.glossary.manager import GlossaryManager

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_create_glossary():
    async with async_session() as db:
        manager = GlossaryManager(db)
        glossary = await manager.create("News Terms", "Terms for news broadcasts", created_by=1)
        assert glossary.id is not None
        assert glossary.name == "News Terms"

@pytest.mark.asyncio
async def test_add_entries():
    async with async_session() as db:
        manager = GlossaryManager(db)
        glossary = await manager.create("Test", "", created_by=1)
        await manager.add_entry(glossary.id, "Fed", "聯儲局")
        await manager.add_entry(glossary.id, "APAC", "亞太區")
        entries = await manager.get_entries(glossary.id)
        assert len(entries) == 2
        assert entries[0].source_term == "Fed"

@pytest.mark.asyncio
async def test_delete_entry():
    async with async_session() as db:
        manager = GlossaryManager(db)
        glossary = await manager.create("Test", "", created_by=1)
        entry = await manager.add_entry(glossary.id, "Fed", "聯儲局")
        await manager.delete_entry(entry.id)
        entries = await manager.get_entries(glossary.id)
        assert len(entries) == 0

@pytest.mark.asyncio
async def test_list_glossaries():
    async with async_session() as db:
        manager = GlossaryManager(db)
        await manager.create("Glossary A", "", created_by=1)
        await manager.create("Glossary B", "", created_by=1)
        glossaries = await manager.list_all()
        assert len(glossaries) == 2

@pytest.mark.asyncio
async def test_get_entries_as_dict():
    async with async_session() as db:
        manager = GlossaryManager(db)
        glossary = await manager.create("Test", "", created_by=1)
        await manager.add_entry(glossary.id, "Fed", "聯儲局")
        await manager.add_entry(glossary.id, "APAC", "亞太區")
        term_dict = await manager.get_entries_as_dict(glossary.id)
        assert term_dict == {"Fed": "聯儲局", "APAC": "亞太區"}
