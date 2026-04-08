"""Glossary CRUD operations."""
from typing import Dict, List, Optional
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from features.glossary.models import Glossary, GlossaryEntry

class GlossaryManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, description: str, created_by: int) -> Glossary:
        glossary = Glossary(name=name, description=description, created_by=created_by)
        self.db.add(glossary)
        await self.db.commit()
        await self.db.refresh(glossary)
        return glossary

    async def get(self, glossary_id: int) -> Optional[Glossary]:
        result = await self.db.execute(select(Glossary).where(Glossary.id == glossary_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Glossary]:
        result = await self.db.execute(select(Glossary).order_by(Glossary.created_at.desc()))
        return list(result.scalars().all())

    async def delete(self, glossary_id: int) -> bool:
        glossary = await self.get(glossary_id)
        if glossary is None:
            return False
        await self.db.execute(delete(GlossaryEntry).where(GlossaryEntry.glossary_id == glossary_id))
        await self.db.delete(glossary)
        await self.db.commit()
        return True

    async def add_entry(self, glossary_id: int, source_term: str, target_term: str) -> GlossaryEntry:
        entry = GlossaryEntry(glossary_id=glossary_id, source_term=source_term, target_term=target_term)
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def delete_entry(self, entry_id: int) -> bool:
        result = await self.db.execute(select(GlossaryEntry).where(GlossaryEntry.id == entry_id))
        entry = result.scalar_one_or_none()
        if entry is None:
            return False
        await self.db.delete(entry)
        await self.db.commit()
        return True

    async def get_entries(self, glossary_id: int) -> List[GlossaryEntry]:
        result = await self.db.execute(select(GlossaryEntry).where(GlossaryEntry.glossary_id == glossary_id))
        return list(result.scalars().all())

    async def get_entries_as_dict(self, glossary_id: int) -> Dict[str, str]:
        entries = await self.get_entries(glossary_id)
        return {e.source_term: e.target_term for e in entries}
