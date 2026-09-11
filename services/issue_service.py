"""Service layer encapsulating database transactions, dynamic issue persistence,
and closed-loop mobile tracking."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.models.issue import Issue
from backend.schemas.ai import MultimodalAnalysisRequest
from backend.schemas.issue import IssueCreate, IssueStatusUpdate, IssueSubmitRequest
from backend.services.ai_service import process_multimodal_fusion
from backend.services.priority_service import evaluate_issue_priority


def create_issue(db: Session, payload: IssueCreate) -> Issue:
    """Standard issue insertion."""
    issue_data = payload.model_dump()
    new_issue = Issue(**issue_data)
    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)
    return new_issue


def submit_and_analyze_unified_issue(db: Session, payload: IssueSubmitRequest) -> Issue:
    """Unified multimodal intake: saves text, audio, uploaded evidence, phone number,
    and runs dynamic spatial-deficit priority evaluation."""
    primary_text = (payload.text or payload.voice_transcript or "").strip()

    # 1. Run Multimodal Signal Fusion
    fusion_req = MultimodalAnalysisRequest(
        text=payload.text,
        voice_transcript=payload.voice_transcript,
        vision_category=payload.vision_category,
        vision_evidence_signal=payload.vision_evidence_signal,
        vision_observations=getattr(payload, "vision_observations", None),
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_name=payload.location_name,
    )
    fusion_res = process_multimodal_fusion(fusion_req)

    # 2. Dynamic Priority Evaluation
    score, level, _, _ = evaluate_issue_priority(
        category=fusion_res.category,
        evidence_strength=fusion_res.evidence_signal,
        latitude=payload.latitude,
        longitude=payload.longitude,
        db=db,
    )

    now_utc = datetime.now(timezone.utc)

    # 3. Clean and normalize 10-digit mobile number
    clean_phone: Optional[str] = None
    raw_phone = getattr(payload, "phone", None)
    if raw_phone:
        digits = "".join(filter(str.isdigit, str(raw_phone)))
        if len(digits) >= 10:
            clean_phone = digits[-10:]
        elif digits:
            clean_phone = digits

    # 4. Construct Persistent Database Record
    new_issue = Issue(
        category=fusion_res.category,
        text=primary_text if primary_text else None,
        input_type=payload.input_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_name=payload.location_name or "Bhubaneswar",
        phone=clean_phone,
        timestamp=now_utc,
        image_path=payload.image_path,
        audio_path=payload.audio_path,
        priority_score=float(score),
        status="analyzed",
        ai_category=fusion_res.category,
        ai_intent=fusion_res.intent,
        ai_summary=(
            fusion_res.text_analysis.summary
            if fusion_res.text_analysis
            else primary_text[:140]
        ),
        ai_confidence=(
            fusion_res.text_analysis.confidence if fusion_res.text_analysis else 0.85
        ),
        ai_observation=fusion_res.ai_observation,
        priority_level=level,
        evidence_strength=fusion_res.evidence_signal,
        analysis_mode=fusion_res.analysis_mode,
        analyzed_at=now_utc,
        created_at=now_utc,
        updated_at=now_utc,
    )

    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)
    return new_issue


def get_issue_by_id(db: Session, issue_id: int) -> Optional[Issue]:
    """Fetches a single issue by primary key."""
    return db.query(Issue).filter(Issue.id == issue_id).first()


def list_issues(
    db: Session,
    category: Optional[str] = None,
    status: Optional[str] = None,
    phone: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[int, List[Issue]]:
    """Lists issues with strict filtering by category, status, and mobile number."""
    query = db.query(Issue)

    if category:
        query = query.filter(Issue.category == category)
    if status:
        query = query.filter(Issue.status == status)

    if phone:
        clean_phone = "".join(filter(str.isdigit, str(phone)))[-10:]
        if clean_phone:
            query = query.filter(
                Issue.phone.isnot(None),
                Issue.phone.like(f"%{clean_phone}%"),
            )
        else:
            return 0, []

    total = query.count()
    items = query.order_by(Issue.created_at.desc()).offset(offset).limit(limit).all()
    return total, items


def update_issue_status(
    db: Session, issue_id: int, payload: IssueStatusUpdate
) -> Optional[Issue]:
    """Updates lifecycle status from Government Command Center."""
    issue = get_issue_by_id(db, issue_id)
    if not issue:
        return None

    setattr(issue, "status", payload.status)
    setattr(issue, "updated_at", datetime.now(timezone.utc))
    db.commit()
    db.refresh(issue)
    return issue


def seed_demo_issues(db: Session):
    """Seed zero fake issues. Real production mode starts with 0 data."""
    pass
