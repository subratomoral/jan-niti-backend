"""SQLAlchemy model for citizen-reported issues with analytical AI extension fields."""

from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from backend.models.database import Base


class Issue(Base):
    __tablename__ = "issues"

    # Using Any allows both SQL expressions (like Issue.category == val)
    # and instance attribute access (like issue.category = "Roads") without Pyright errors.
    id: Any = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category: Any = Column(String(64), nullable=False, index=True)
    text: Any = Column(Text, nullable=True)
    input_type: Any = Column(String(32), nullable=False)
    latitude: Any = Column(Float, nullable=True)
    longitude: Any = Column(Float, nullable=True)
    location_name: Any = Column(String(128), nullable=True)
    phone: Any = Column(String(20), nullable=True, index=True)
    timestamp: Any = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    image_path: Any = Column(String(256), nullable=True)
    audio_path: Any = Column(String(256), nullable=True)
    priority_score: Any = Column(Float, nullable=True)
    status: Any = Column(String(32), default="submitted", nullable=False, index=True)

    # Extended AI Pipeline Persistence Fields
    ai_category: Any = Column(String(64), nullable=True)
    ai_intent: Any = Column(String(128), nullable=True)
    ai_summary: Any = Column(Text, nullable=True)
    ai_confidence: Any = Column(Float, nullable=True)
    ai_observation: Any = Column(Text, nullable=True)
    priority_level: Any = Column(String(16), nullable=True)
    evidence_strength: Any = Column(Float, nullable=True)
    analysis_mode: Any = Column(String(16), default="demo", nullable=False)
    analyzed_at: Any = Column(DateTime(timezone=True), nullable=True)

    created_at: Any = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Any = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
