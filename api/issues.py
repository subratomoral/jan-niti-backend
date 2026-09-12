from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from models.database import get_db
from schemas.ai import IssueAnalysisResponse
from schemas.issue import (
    IssueCreate,
    IssueListResponse,
    IssueResponse,
    IssueStatusUpdate,
    IssueSubmitRequest,
)
from services import ai_service, issue_service

router = APIRouter(prefix="/api/issues", tags=["Issues"])


@router.post(
    "/submit",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Unified Multimodal Issue Submission",
)
def submit_issue(payload: IssueSubmitRequest, db: Session = Depends(get_db)):
    if (
        not (payload.text and payload.text.strip())
        and not (payload.voice_transcript and payload.voice_transcript.strip())
        and not payload.image_path
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot submit an issue without text, voice transcript, or photo evidence.",
        )
    return issue_service.submit_and_analyze_unified_issue(db, payload)


@router.post(
    "",
    response_model=IssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Standard Issue Creation",
)
def post_issue(payload: IssueCreate, db: Session = Depends(get_db)):
    return issue_service.create_issue(db, payload)


@router.post(
    "/{issue_id}/analyze",
    response_model=IssueAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run AI Analysis on Stored Issue",
)
def analyze_stored_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = issue_service.get_issue_by_id(db, issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with ID {issue_id} not found",
        )
    return ai_service.analyze_and_persist_issue(db, issue)


@router.get(
    "",
    response_model=IssueListResponse,
    summary="List Issues with Strict Filtering",
)
def get_issues(
    category: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    phone: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total, items = issue_service.list_issues(
        db,
        category=category,
        status=status,
        phone=phone,
        limit=limit,
        offset=offset,
    )
    return IssueListResponse(
        total=total,
        items=[IssueResponse.model_validate(item) for item in items],
    )


@router.get(
    "/{issue_id}",
    response_model=IssueResponse,
    summary="Get Single Issue",
)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = issue_service.get_issue_by_id(db, issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with ID {issue_id} not found",
        )
    return issue


@router.patch(
    "/{issue_id}/status",
    response_model=IssueResponse,
    summary="Update Issue Status",
)
def patch_issue_status(
    issue_id: int,
    payload: IssueStatusUpdate,
    db: Session = Depends(get_db),
):
    updated = issue_service.update_issue_status(db, issue_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue with ID {issue_id} not found",
        )
    return updated
