"""Glossary database models."""
import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Glossary(Base):
    __tablename__ = "glossaries"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

class GlossaryEntry(Base):
    __tablename__ = "glossary_entries"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    glossary_id: Mapped[int] = mapped_column(Integer, ForeignKey("glossaries.id", ondelete="CASCADE"), nullable=False)
    source_term: Mapped[str] = mapped_column(String(500), nullable=False)
    target_term: Mapped[str] = mapped_column(String(500), nullable=False)
