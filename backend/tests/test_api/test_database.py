import pytest
import pytest_asyncio
from sqlalchemy import select

from app.database import async_engine, async_session, Base
from app.models.user import User


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_user():
    async with async_session() as session:
        user = User(name="alice", password_hash="hashed123")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        assert user.id is not None
        assert user.name == "alice"
        assert user.created_at is not None


@pytest.mark.asyncio
async def test_unique_username():
    async with async_session() as session:
        session.add(User(name="bob", password_hash="hash1"))
        await session.commit()
    with pytest.raises(Exception):
        async with async_session() as session:
            session.add(User(name="bob", password_hash="hash2"))
            await session.commit()
