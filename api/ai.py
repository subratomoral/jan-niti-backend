"""FastAPI router exposing Speech Transcription, Vision Analysis, and Multimodal Fusion APIs."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.schemas.ai import (
    MultimodalAnalysisRequest,
    MultimodalAnalysisResponse,
    SpeechTranscriptionResponse,
    TextAnalysisRequest,
    TextAnalysisResponse,
    ThemeClusteringResponse,
    VisionAnalysisResponse,
)
from backend.services import (
    ai_service,
    clustering_service,
    speech_service,
    vision_service,
)

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post(
    "/transcribe",
    response_model=SpeechTranscriptionResponse,
    summary="8B: Speech-to-Text Transcription",
    description="Transcribes citizen audio upload with validation and fallback handling.",
)
async def transcribe_audio(file: UploadFile = File(...)):
    return await speech_service.transcribe_audio_file(file)


@router.post(
    "/analyze-image",
    response_model=VisionAnalysisResponse,
    summary="8G: Image/Vision Evidence Analysis",
    description="Processes uploaded photographic evidence and extracts factual visual observations.",
)
async def analyze_image(file: UploadFile = File(...)):
    return await vision_service.analyze_photo_evidence(file)


@router.post(
    "/analyze-multimodal",
    response_model=MultimodalAnalysisResponse,
    summary="8L: Multimodal Signal Fusion",
    description="Fuses text, voice transcript, image observations, and location into a unified issue context.",
)
def analyze_multimodal(payload: MultimodalAnalysisRequest):
    return ai_service.process_multimodal_fusion(payload)


@router.get(
    "/themes",
    response_model=ThemeClusteringResponse,
    summary="Theme Clusters",
    description="Aggregates citizen reports into categorical themes directly from the database.",
)
def get_themes(category: str = "Healthcare", db: Session = Depends(get_db)):
    return clustering_service.get_theme_clusters(category, db=db)


@router.post(
    "/analyze",
    response_model=TextAnalysisResponse,
    summary="Text NLP Analysis",
    description="Processes citizen natural language text to extract category, intent, summary, and priority signal.",
)
def analyze_text(payload: TextAnalysisRequest):
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text input cannot be empty or solely whitespace.",
        )
    return ai_service.analyze_issue_text(payload.text)
