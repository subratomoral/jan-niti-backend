"""Services package exporting all core AI, priority, vision, audio, and database operations."""

from backend.services.ai_service import (
    analyze_and_persist_issue,
    analyze_issue_text,
    analyze_issue_text_with_llm,
    process_multimodal_fusion,
    safe_extract_json,
)
from backend.services.clustering_service import get_theme_clusters
from backend.services.geo_service import evaluate_geo_context
from backend.services.issue_service import (
    create_issue,
    get_issue_by_id,
    list_issues,
    seed_demo_issues,
    submit_and_analyze_unified_issue,
    update_issue_status,
)
from backend.services.priority_service import (
    calculate_priority_score,
    compute_evidence_strength,
    evaluate_issue_priority,
)
from backend.services.similarity_service import calculate_similar_reports
from backend.services.speech_service import (
    transcribe_audio,
    transcribe_audio_file,
)
from backend.services.vision_service import (
    analyze_image_evidence,
    analyze_photo_evidence,
)

__all__ = [
    # Issue DB Services
    "create_issue",
    "submit_and_analyze_unified_issue",
    "get_issue_by_id",
    "list_issues",
    "update_issue_status",
    "seed_demo_issues",
    # AI NLP & Multimodal Fusion
    "analyze_issue_text",
    "analyze_issue_text_with_llm",
    "analyze_and_persist_issue",
    "process_multimodal_fusion",
    "safe_extract_json",
    # Speech Services
    "transcribe_audio",
    "transcribe_audio_file",
    # Vision Services
    "analyze_image_evidence",
    "analyze_photo_evidence",
    # Analysis, Geo & Priority
    "calculate_similar_reports",
    "get_theme_clusters",
    "calculate_priority_score",
    "evaluate_issue_priority",
    "compute_evidence_strength",
    "evaluate_geo_context",
]
