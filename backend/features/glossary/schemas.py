"""Glossary Pydantic schemas."""
import datetime
from typing import List
from pydantic import BaseModel

class GlossaryCreate(BaseModel):
    name: str
    description: str = ""

class GlossaryResponse(BaseModel):
    id: int
    name: str
    description: str
    created_by: int
    created_at: datetime.datetime

class EntryCreate(BaseModel):
    source_term: str
    target_term: str

class EntryResponse(BaseModel):
    id: int
    glossary_id: int
    source_term: str
    target_term: str

class EntryBulkCreate(BaseModel):
    entries: List[EntryCreate]
