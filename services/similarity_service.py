"""Similarity service comparing issues against SQLite records."""

from typing import List
from sqlalchemy.orm import Session
from backend.models.issue import Issue
from backend.schemas.ai import SimilarReportMatch, SimilarReportsResponse


def calculate_similar_reports(
    db: Session, text: str, category: str, exclude_issue_id: int = 0
) -> SimilarReportsResponse:
    if not text or not text.strip():
        return SimilarReportsResponse(
            target_text=text or "",
            similar_reports_count=0,
            matches=[],
            analysis_mode="demo",
        )

    tokens = set(text.lower().split())

    # Safely query issues of matching category excluding the current issue
    issues: List[Issue] = (
        db.query(Issue)
        .filter(Issue.category == category, Issue.id != exclude_issue_id)
        .limit(50)
        .all()
    )

    scored_matches: List[SimilarReportMatch] = []

    for item in issues:
        issue_text = str(getattr(item, "text", "") or "").strip()
        if not issue_text:
            continue

        item_tokens = set(issue_text.lower().split())
        intersection = tokens.intersection(item_tokens)
        union = tokens.union(item_tokens)
        score = len(intersection) / len(union) if union else 0.0

        if score > 0.10:
            preview = issue_text[:90] + ("..." if len(issue_text) > 90 else "")
            item_id = int(getattr(item, "id", 0))
            scored_matches.append(
                SimilarReportMatch(
                    issue_id=item_id,
                    text_preview=preview,
                    category=str(getattr(item, "category", category)),
                    similarity_score=round(score, 2),
                )
            )

    scored_matches.sort(key=lambda m: m.similarity_score, reverse=True)
    top_matches = scored_matches[:5]

    return SimilarReportsResponse(
        target_text=text,
        similar_reports_count=len(scored_matches),
        matches=top_matches,
        analysis_mode="live" if scored_matches else "demo",
    )
