"""Translation Memory store — add, lookup (exact + fuzzy)."""
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from features.translation_memory.matcher import fuzzy_match
from features.translation_memory.models import TranslationMemory, text_hash

class TMStore:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, source_text: str, target_text: str, confirmed_by: int) -> TranslationMemory:
        entry = TranslationMemory(source_text=source_text, target_text=target_text, source_hash=text_hash(source_text), confirmed_by=confirmed_by)
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def lookup(self, source_text: str) -> Optional[TranslationMemory]:
        h = text_hash(source_text)
        result = await self.db.execute(select(TranslationMemory).where(TranslationMemory.source_hash == h).limit(1))
        return result.scalar_one_or_none()

    async def fuzzy_lookup(self, source_text: str, threshold: float = 0.85) -> Optional[Dict]:
        exact = await self.lookup(source_text)
        if exact:
            return {"target_text": exact.target_text, "score": 1.0, "id": exact.id}
        result = await self.db.execute(select(TranslationMemory))
        entries = result.scalars().all()
        best_score = 0.0
        best_entry = None
        for entry in entries:
            score = fuzzy_match(source_text, entry.source_text)
            if score > best_score:
                best_score = score
                best_entry = entry
        if best_entry and best_score >= threshold:
            return {"target_text": best_entry.target_text, "score": best_score, "id": best_entry.id}
        return None

    async def bulk_lookup(self, texts: List[str], threshold: float = 0.85) -> Dict[str, Dict]:
        results = {}
        for text in texts:
            match = await self.fuzzy_lookup(text, threshold)
            if match:
                results[text] = match
        return results
