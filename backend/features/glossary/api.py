"""Glossary REST API routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_current_user, get_db
from app.models.user import User
from features.glossary.importer import entries_to_csv, parse_csv
from features.glossary.manager import GlossaryManager
from features.glossary.schemas import EntryBulkCreate, EntryResponse, GlossaryCreate, GlossaryResponse

router = APIRouter(prefix="/api/glossaries", tags=["glossary"])

@router.post("", response_model=GlossaryResponse, status_code=status.HTTP_201_CREATED)
async def create_glossary(body: GlossaryCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    manager = GlossaryManager(db)
    glossary = await manager.create(body.name, body.description, created_by=user.id)
    return GlossaryResponse(id=glossary.id, name=glossary.name, description=glossary.description, created_by=glossary.created_by, created_at=glossary.created_at)

@router.get("", response_model=List[GlossaryResponse])
async def list_glossaries(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    manager = GlossaryManager(db)
    glossaries = await manager.list_all()
    return [GlossaryResponse(id=g.id, name=g.name, description=g.description, created_by=g.created_by, created_at=g.created_at) for g in glossaries]

@router.delete("/{glossary_id}")
async def delete_glossary(glossary_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    manager = GlossaryManager(db)
    deleted = await manager.delete(glossary_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Glossary not found")
    return {"detail": "Glossary deleted"}

@router.post("/{glossary_id}/entries", response_model=List[EntryResponse], status_code=status.HTTP_201_CREATED)
async def add_entries(glossary_id: int, body: EntryBulkCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    manager = GlossaryManager(db)
    glossary = await manager.get(glossary_id)
    if glossary is None:
        raise HTTPException(status_code=404, detail="Glossary not found")
    results = []
    for e in body.entries:
        entry = await manager.add_entry(glossary_id, e.source_term, e.target_term)
        results.append(EntryResponse(id=entry.id, glossary_id=entry.glossary_id, source_term=entry.source_term, target_term=entry.target_term))
    return results

@router.get("/{glossary_id}/entries", response_model=List[EntryResponse])
async def get_entries(glossary_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    manager = GlossaryManager(db)
    entries = await manager.get_entries(glossary_id)
    return [EntryResponse(id=e.id, glossary_id=e.glossary_id, source_term=e.source_term, target_term=e.target_term) for e in entries]

@router.post("/{glossary_id}/import")
async def import_csv(glossary_id: int, file: UploadFile, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    manager = GlossaryManager(db)
    glossary = await manager.get(glossary_id)
    if glossary is None:
        raise HTTPException(status_code=404, detail="Glossary not found")
    content = (await file.read()).decode("utf-8")
    pairs = parse_csv(content)
    for source, target in pairs:
        await manager.add_entry(glossary_id, source, target)
    return {"imported": len(pairs)}

@router.get("/{glossary_id}/export")
async def export_csv(glossary_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    manager = GlossaryManager(db)
    entries = await manager.get_entries(glossary_id)
    if not entries:
        raise HTTPException(status_code=404, detail="No entries to export")
    csv_data = entries_to_csv([{"source_term": e.source_term, "target_term": e.target_term} for e in entries])
    return PlainTextResponse(content=csv_data, media_type="text/csv")
