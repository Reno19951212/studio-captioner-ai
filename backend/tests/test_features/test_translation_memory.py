import pytest
import pytest_asyncio
from app.database import Base, async_engine, async_session
from features.translation_memory.matcher import fuzzy_match
from features.translation_memory.store import TMStore

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

class TestFuzzyMatcher:
    def test_exact_match(self):
        assert fuzzy_match("The Fed announced today", "The Fed announced today") == 1.0

    def test_similar_match(self):
        assert fuzzy_match("The Fed announced today", "The Fed announced yesterday") > 0.7

    def test_different_text(self):
        assert fuzzy_match("Hello world", "Completely different text here") < 0.5

    def test_empty_text(self):
        assert fuzzy_match("", "") == 1.0

class TestTMStore:
    @pytest.mark.asyncio
    async def test_store_and_exact_lookup(self):
        async with async_session() as db:
            store = TMStore(db)
            await store.add("The Fed announced today", "聯儲局今日宣佈", confirmed_by=1)
            result = await store.lookup("The Fed announced today")
            assert result is not None
            assert result.target_text == "聯儲局今日宣佈"

    @pytest.mark.asyncio
    async def test_fuzzy_lookup(self):
        async with async_session() as db:
            store = TMStore(db)
            await store.add("The Fed announced today", "聯儲局今日宣佈", confirmed_by=1)
            result = await store.fuzzy_lookup("The Fed announced yesterday", threshold=0.7)
            assert result is not None
            assert result["target_text"] == "聯儲局今日宣佈"

    @pytest.mark.asyncio
    async def test_fuzzy_lookup_no_match(self):
        async with async_session() as db:
            store = TMStore(db)
            await store.add("Hello world", "你好世界", confirmed_by=1)
            result = await store.fuzzy_lookup("Completely different sentence", threshold=0.85)
            assert result is None

    @pytest.mark.asyncio
    async def test_bulk_lookup(self):
        async with async_session() as db:
            store = TMStore(db)
            await store.add("Hello world", "你好世界", confirmed_by=1)
            await store.add("Good morning", "早晨好", confirmed_by=1)
            results = await store.bulk_lookup(["Hello world", "Good morning", "Unknown text"], threshold=0.85)
            assert results["Hello world"]["target_text"] == "你好世界"
            assert results["Good morning"]["target_text"] == "早晨好"
            assert "Unknown text" not in results
