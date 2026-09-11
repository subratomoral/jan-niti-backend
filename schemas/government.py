"""Pydantic schemas for Government Command Portal API responses."""

from typing import Literal
from pydantic import BaseModel, Field

PriorityLevelType = Literal["HIGH", "MEDIUM", "LOW"]
DataModeType = Literal["live", "demo"]


class GovernmentPrioritySummaryItem(BaseModel):
    category: str = Field(..., description="Civic sector category")
    priority_score: int = Field(..., ge=0, le=100, description="Priority score")
    priority_level: PriorityLevelType = Field(
        ..., description="Priority severity level"
    )
    report_count: int = Field(default=0, ge=0, description="Total reports aggregated")
    high_priority_count: int = Field(
        default=0, ge=0, description="Count of high priority items"
    )


class GovernmentOverviewResponse(BaseModel):
    total_submissions: int = Field(default=0, ge=0)
    live_submissions_count: int = Field(default=0, ge=0)
    constituencies_analysed: int = Field(default=0, ge=0)
    active_hotspots: int = Field(default=0, ge=0)
    high_priority_issues: int = Field(default=0, ge=0)
    data_mode: DataModeType = "live"
    data_source_label: str = "Live Database"


class GovernmentConstituencyResponse(BaseModel):
    name: str = "Bhubaneswar"
    state: str = "Odisha"
    district: str = "Khordha"
    population: int = Field(default=0, ge=0)
    citizen_reports: int = Field(default=0, ge=0)
    live_citizen_reports: int = Field(default=0, ge=0)
    high_priority: int = Field(default=0, ge=0)
    active_hotspots: int = Field(default=0, ge=0)
    data_mode: DataModeType = "live"
    data_source_label: str = "Live Database"


class GovernmentHotspotItem(BaseModel):
    id: str
    category: str
    title: str
    area: str
    latitude: float
    longitude: float
    reports: int = Field(default=0, ge=0)
    population: int = Field(default=0, ge=0)
    facilities: int = Field(default=0, ge=0)
    priority: int = Field(default=0, ge=0, le=100)


class GovernmentThemeItem(BaseModel):
    category: str
    theme: str
    count: int = Field(default=0, ge=0)
