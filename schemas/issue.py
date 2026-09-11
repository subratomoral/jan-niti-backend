"""Pydantic schemas for unified issue submission, validation, updates, and enriched serialization."""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

CategoryType = Literal[
    "Healthcare",
    "Roads",
    "Education",
    "Water",
    "Employment",
    "Community Development",
    "Other",
]

StatusType = Literal[
    "submitted",
    "processing",
    "analyzed",
    "under_review",
    "verified",
    "resolved",
]

InputType = Literal[
    "text",
    "voice",
    "photo",
    "voice+text",
    "voice+photo",
    "text+photo",
    "voice+text+photo",
]

AnalysisModeType = Literal["live", "demo", "fallback", "ai"]


class IssueSubmitRequest(BaseModel):
    text: Optional[str] = Field(
        default=None, max_length=2000, description="Citizen text report"
    )
    voice_transcript: Optional[str] = Field(
        default=None, max_length=2000, description="Transcribed audio speech"
    )
    input_type: InputType = Field(default="text", description="Input channels used")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    location_name: Optional[str] = Field(default=None, max_length=128)
    image_path: Optional[str] = Field(default=None, max_length=256)
    audio_path: Optional[str] = Field(default=None, max_length=256)
    vision_category: Optional[CategoryType] = None
    vision_evidence_signal: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    vision_observations: Optional[List[str]] = None


class IssueCreate(BaseModel):
    category: CategoryType = Field(default="Community Development")
    text: Optional[str] = Field(default=None, max_length=2000)
    input_type: InputType = Field(default="text")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    location_name: Optional[str] = Field(default=None, max_length=128)
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    priority_score: Optional[float] = None


class IssueStatusUpdate(BaseModel):
    status: StatusType = Field(..., description="Lifecycle status update")


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    text: Optional[str] = None
    input_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    timestamp: datetime
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    priority_score: Optional[float] = None
    status: str

    ai_category: Optional[str] = None
    ai_intent: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_observation: Optional[str] = None
    priority_level: Optional[str] = None
    evidence_strength: Optional[float] = None
    analysis_mode: AnalysisModeType = "demo"
    analyzed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class IssueListResponse(BaseModel):
    total: int
    items: List[IssueResponse]
