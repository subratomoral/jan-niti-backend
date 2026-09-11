"""Pydantic schemas for the complete JAN-NITI AI Pipeline & Multimodal Input Processing."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

CategoryType = Literal[
    "Healthcare",
    "Roads",
    "Education",
    "Water",
    "Employment",
    "Community Development",
    "Other",
]

PrioritySignalType = Literal["high", "medium", "low"]
PriorityLevelType = Literal["HIGH", "MEDIUM", "LOW"]
AnalysisModeType = Literal["live", "demo", "fallback", "ai"]


# 6A: Text Intelligence
class TextAnalysisRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Citizen report text in English, Hindi, or Hinglish.",
        examples=[
            "There is no hospital near our village and emergency patients have to travel very far."
        ],
    )


class TextAnalysisResponse(BaseModel):
    category: CategoryType = Field(..., description="Detected category domain")
    intent: str = Field(
        ..., description="Specific civic intent extracted from the issue"
    )
    summary: str = Field(..., description="Concise structured problem summary")
    priority_signal: PrioritySignalType = Field(
        ..., description="Heuristic priority signal"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    ai_observation: str = Field(..., description="Analytical civic observation")
    analysis_mode: AnalysisModeType = Field(
        default="demo", description="'live', 'demo', 'fallback', or 'ai'"
    )


# 6B: Speech-to-Text
class SpeechTranscriptionResponse(BaseModel):
    text: str = Field(..., description="Extracted transcript from citizen audio")
    language: str = Field(
        default="en", description="Detected language code (e.g. en, hi)"
    )
    confidence: float = Field(
        default=0.90, ge=0.0, le=1.0, description="Transcription confidence score"
    )
    analysis_mode: AnalysisModeType = Field(
        default="demo", description="'live', 'demo', or 'fallback'"
    )


# 6C: Vision Analysis
class VisionAnalysisResponse(BaseModel):
    possible_category: CategoryType = Field(
        ..., description="Estimated civic category from visual indicators"
    )
    observations: List[str] = Field(
        ..., description="Structured factual visual observations"
    )
    evidence_signal: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Evidence weight from visual clarity (0.0 - 1.0)",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Vision model confidence"
    )
    analysis_mode: AnalysisModeType = Field(
        default="demo", description="'live', 'demo', or 'fallback'"
    )


# 6D: Similar Report Detection
class SimilarReportMatch(BaseModel):
    issue_id: int
    text_preview: str
    category: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class SimilarReportsResponse(BaseModel):
    target_text: str
    similar_reports_count: int
    matches: List[SimilarReportMatch]
    analysis_mode: AnalysisModeType = Field(default="demo")


# 6E: Theme Clustering
class ThemeClusterItem(BaseModel):
    name: str
    count: int
    percentage: float


class ThemeClusteringResponse(BaseModel):
    category: str
    total_analyzed: int
    themes: List[ThemeClusterItem]
    analysis_mode: AnalysisModeType = Field(default="demo")


# 6F: Priority Engine Breakdown
class PriorityFactorBreakdown(BaseModel):
    citizen_demand: float
    people_affected: float
    infrastructure_gap: float
    social_impact: float
    economic_impact: float


class PriorityEngineResponse(BaseModel):
    priority_score: int = Field(..., ge=0, le=100)
    level: PriorityLevelType
    factors: PriorityFactorBreakdown
    explanation: str
    analysis_mode: AnalysisModeType = Field(default="demo")


# 6G: Geo Context
class GeoFacilityContext(BaseModel):
    nearest_facility_name: str
    nearest_facility_distance_km: float
    facilities_within_2km: int
    population_density_est: int
    area_hotspot_level: Literal["High", "Medium", "Low"]


class GeoAnalysisResponse(BaseModel):
    latitude: float
    longitude: float
    location_name: Optional[str] = None
    geo_context: GeoFacilityContext
    analysis_mode: AnalysisModeType = Field(default="demo")


# 7A/9A: Issue Analysis & Pipeline Schemas
class IssueAnalysisResponse(BaseModel):
    issue_id: int
    category: CategoryType
    intent: str
    summary: str
    confidence: float
    priority_signal: PrioritySignalType
    priority_score: int
    priority_level: PriorityLevelType
    factor_breakdown: PriorityFactorBreakdown
    evidence_strength: float
    ai_observation: str
    recommended_verification: str = "Field verification recommended"
    analysis_mode: AnalysisModeType = "demo"
    analyzed_at: datetime


# 8L: Multimodal Fusion Schemas
class TextAnalysisSummary(BaseModel):
    category: CategoryType
    intent: str
    summary: str
    confidence: float


class MultimodalLocationSummary(BaseModel):
    available: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None


class MultimodalAnalysisRequest(BaseModel):
    text: Optional[str] = Field(default=None, max_length=2000)
    voice_transcript: Optional[str] = Field(default=None, max_length=2000)
    vision_category: Optional[CategoryType] = None
    vision_evidence_signal: Optional[float] = None
    vision_observations: Optional[List[str]] = None
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    location_name: Optional[str] = None


class MultimodalAnalysisResponse(BaseModel):
    category: CategoryType
    intent: str
    text_analysis: Optional[TextAnalysisSummary] = None
    speech_analysis: Optional[SpeechTranscriptionResponse] = None
    vision_analysis: Optional[VisionAnalysisResponse] = None
    location: MultimodalLocationSummary
    evidence_signal: float = Field(..., ge=0.0, le=1.0)
    priority_signal: float = Field(..., ge=0.0, le=1.0)
    consistency_flag: Literal["consistent", "conflict", "single_source"] = "consistent"
    consistency_message: Optional[str] = None
    ai_observation: str
    analysis_mode: AnalysisModeType = Field(default="demo")
