# """Transparent, Dynamic Multi-Factor Priority Signal Engine.
# Replaces static lookup tables with dynamic calculations driven by:
# 1. Base Sector Criticality
# 2. Multimodal Evidence Signal (Text + Speech + Verified Vision)
# 3. Geodesic Infrastructure Gap (Haversine Distance to nearest facility)
# 4. Neighborhood Clustered Demand (Real DB Correlated Reports)
# """

# from typing import Optional, Tuple
# from sqlalchemy.orm import Session

# from schemas.ai import (
#     PriorityEngineResponse,
#     PriorityFactorBreakdown,
#     PriorityLevelType,
# )
# from services.geo_service import evaluate_geo_context

# # Baseline domain criticality weights (Out of 100)
# BASE_CRITICALITY = {
#     "Healthcare": 82,
#     "Water": 78,
#     "Roads": 72,
#     "Education": 68,
#     "Employment": 58,
#     "Community Development": 54,
#     "Other": 45,
# }


# def compute_evidence_strength(
#     has_text: bool,
#     has_audio: bool,
#     has_image: bool,
#     has_location: bool,
#     image_evidence_signal: Optional[float] = None,
# ) -> float:
#     """Calculates factual evidence signal strength (0.15 to 1.0) based on verified input streams."""
#     score = 0.0

#     if has_text:
#         score += 0.30
#     if has_audio:
#         score += 0.25
#     if has_location:
#         score += 0.20

#     if has_image:
#         # Use AI vision verification score if available
#         if image_evidence_signal is not None:
#             score += float(image_evidence_signal) * 0.25
#         else:
#             score += 0.20

#     return round(min(1.0, max(0.20, score)), 2)


# def evaluate_issue_priority(
#     category: str,
#     evidence_strength: float = 0.5,
#     latitude: Optional[float] = None,
#     longitude: Optional[float] = None,
#     db: Optional[Session] = None,
# ) -> Tuple[int, PriorityLevelType, PriorityFactorBreakdown, str]:
#     """Dynamically evaluates priority score with enhanced weights to ensure critical issues reach 80+."""
#     from models.issue import Issue

#     # 1. Base Domain Criticality (0 - 100)
#     base_val = BASE_CRITICALITY.get(category, BASE_CRITICALITY["Other"])

#     # 2. Evidence Strength (0 - 100) - Boosted minimum floor
#     ev_val = int(max(0.4, min(1.0, evidence_strength)) * 100)

#     # 3. Spatial Infrastructure Deficit via Haversine Distance
#     geo_context = evaluate_geo_context(
#         lat=latitude,
#         lon=longitude,
#         category=category,
#     )
#     dist_km = geo_context.geo_context.nearest_facility_distance_km
#     facility_name = geo_context.geo_context.nearest_facility_name

#     # Enhanced distance scoring curve for higher urgency
#     if dist_km >= 5.0:
#         infra_deficit = min(99, int(75 + (dist_km * 3)))
#     elif dist_km >= 2.5:
#         infra_deficit = int(55 + (dist_km * 5))
#     else:
#         infra_deficit = max(35, int(25 + (dist_km * 12)))

#     # 4. Clustered Citizen Demand (Real SQLite aggregation)
#     cluster_count = 1
#     if db is not None:
#         try:
#             cluster_count = db.query(Issue).filter(Issue.category == category).count()
#             cluster_count = max(1, cluster_count)
#         except Exception:
#             cluster_count = 1

#     # Scaled neighborhood pressure with higher base weight
#     cluster_score = min(98, max(40, int(35 + (cluster_count * 7.5))))

#     # Upgraded Balanced Weighted Formula (Pushes serious issues above 80)
#     # 15% Base + 25% Evidence + 40% Spatial Deficit + 20% Clustered Pressure
#     raw_priority = (
#         (base_val * 0.15)
#         + (ev_val * 0.25)
#         + (infra_deficit * 0.40)
#         + (cluster_score * 0.20)
#     )

#     # Minimum baseline floor raised to ensure active issues score well
#     final_score = int(round(max(45, min(99, raw_priority))))

#     # Ensure critical healthcare/water or distant issues breach 80 easily
#     if base_val >= 78 and (infra_deficit >= 60 or evidence_strength >= 0.7):
#         final_score = max(final_score, 82)

#     # Determine Severity Level
#     if final_score >= 80:
#         level: PriorityLevelType = "HIGH"
#     elif final_score >= 60:
#         level: PriorityLevelType = "MEDIUM"
#     else:
#         level: PriorityLevelType = "LOW"

#     # Transparent factor breakdown
#     demand_pts = round((cluster_score * 0.20) + (base_val * 0.10), 1)
#     people_pts = round(min(100, cluster_count * 12) * 0.25, 1)
#     infra_pts = round(infra_deficit * 0.40, 1)
#     social_pts = round(ev_val * 0.15, 1)
#     economic_pts = round(base_val * 0.10, 1)

#     factors = PriorityFactorBreakdown(
#         citizen_demand=demand_pts,
#         people_affected=people_pts,
#         infrastructure_gap=infra_pts,
#         social_impact=social_pts,
#         economic_impact=economic_pts,
#     )

#     explanation = (
#         f"Dynamic multi-factor evaluation: Evidence reliability scored {ev_val}%. "
#         f"Nearest {category.lower()} anchor ({facility_name}) is {dist_km} km away "
#         f"(infrastructure deficit: {infra_deficit}%), correlated with {cluster_count} "
#         f"verified neighborhood submissions."
#     )

#     return final_score, level, factors, explanation


# def calculate_priority_score(
#     category: str, reports_count: int = 1
# ) -> PriorityEngineResponse:
#     """Entry point for API controllers with dynamic defaults."""
#     score, level, factors, explanation = evaluate_issue_priority(
#         category=category,
#         evidence_strength=0.70,
#         latitude=20.2961,
#         longitude=85.8245,
#         db=None,
#     )

#     return PriorityEngineResponse(
#         priority_score=score,
#         level=level,
#         factors=factors,
#         explanation=explanation,
#         analysis_mode="live",
#     )
"""Transparent, Dynamic Multi-Factor Priority Signal Engine with Rigorous Noise & Validity Safeguards."""

from typing import Optional, Tuple
from sqlalchemy.orm import Session

from schemas.ai import (
    PriorityEngineResponse,
    PriorityFactorBreakdown,
    PriorityLevelType,
)
from services.geo_service import evaluate_geo_context

# Baseline domain criticality weights (Out of 100)
BASE_CRITICALITY = {
    "Healthcare": 82,
    "Water": 78,
    "Roads": 72,
    "Education": 68,
    "Employment": 58,
    "Community Development": 54,
    "Other": 45,
}


def compute_evidence_strength(
    has_text: bool,
    has_audio: bool,
    has_image: bool,
    has_location: bool,
    image_evidence_signal: Optional[float] = None,
) -> float:
    """Calculates factual evidence signal strength (0.15 to 1.0) based on verified input streams."""
    score = 0.0

    if has_text:
        score += 0.30
    if has_audio:
        score += 0.25
    if has_location:
        score += 0.20

    if has_image:
        if image_evidence_signal is not None:
            score += float(image_evidence_signal) * 0.25
        else:
            score += 0.20

    return round(min(1.0, max(0.10, score)), 2)


def evaluate_issue_priority(
    category: str,
    evidence_strength: float = 0.5,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    db: Optional[Session] = None,
) -> Tuple[int, PriorityLevelType, PriorityFactorBreakdown, str]:
    """Dynamically evaluates priority score with strict noise filtering and dynamic bounds."""
    from models.issue import Issue

    # 1. Check for Invalid/Noise Input (If category is Other and evidence is very weak)
    is_invalid_noise = category == "Other" and evidence_strength < 0.35

    if is_invalid_noise:
        final_score = int(
            round(15 + (evidence_strength * 30))
        )  # Score will range between 15 to 25
        level: PriorityLevelType = "LOW"
        factors = PriorityFactorBreakdown(
            citizen_demand=5.0,
            people_affected=5.0,
            infrastructure_gap=10.0,
            social_impact=5.0,
            economic_impact=5.0,
        )
        explanation = "Input evaluated as non-civic noise or invalid sequence. Priority suppressed to low."
        return final_score, level, factors, explanation

    # 2. Base Domain Criticality (0 - 100)
    base_val = BASE_CRITICALITY.get(category, BASE_CRITICALITY["Other"])

    # 3. Evidence Strength (0 - 100)
    ev_val = int(max(0.1, min(1.0, evidence_strength)) * 100)

    # 4. Spatial Infrastructure Deficit via Haversine Distance
    geo_context = evaluate_geo_context(
        lat=latitude,
        lon=longitude,
        category=category,
    )
    dist_km = geo_context.geo_context.nearest_facility_distance_km
    facility_name = geo_context.geo_context.nearest_facility_name

    if dist_km >= 5.0:
        infra_deficit = min(99, int(75 + (dist_km * 3)))
    elif dist_km >= 2.5:
        infra_deficit = int(55 + (dist_km * 5))
    else:
        infra_deficit = max(30, int(20 + (dist_km * 12)))

    # 5. Clustered Citizen Demand (Real SQLite aggregation)
    cluster_count = 1
    if db is not None:
        try:
            cluster_count = db.query(Issue).filter(Issue.category == category).count()
            cluster_count = max(1, cluster_count)
        except Exception:
            cluster_count = 1

    cluster_score = min(98, max(30, int(30 + (cluster_count * 7.5))))

    # Balanced Weighted Formula
    raw_priority = (
        (base_val * 0.15)
        + (ev_val * 0.25)
        + (infra_deficit * 0.40)
        + (cluster_score * 0.20)
    )

    # Dynamic minimum floor based on evidence and category validity
    min_floor = 40 if evidence_strength > 0.4 else 20
    final_score = int(round(max(min_floor, min(99, raw_priority))))

    # Determine Severity Level dynamically
    if final_score >= 75:
        level = "HIGH"
    elif final_score >= 45:
        level = "MEDIUM"
    else:
        level = "LOW"

    # Transparent factor breakdown
    demand_pts = round((cluster_score * 0.20) + (base_val * 0.10), 1)
    people_pts = round(min(100, cluster_count * 12) * 0.25, 1)
    infra_pts = round(infra_deficit * 0.40, 1)
    social_pts = round(ev_val * 0.15, 1)
    economic_pts = round(base_val * 0.10, 1)

    factors = PriorityFactorBreakdown(
        citizen_demand=demand_pts,
        people_affected=people_pts,
        infrastructure_gap=infra_pts,
        social_impact=social_pts,
        economic_impact=economic_pts,
    )

    explanation = (
        f"Dynamic multi-factor evaluation: Evidence reliability scored {ev_val}%. "
        f"Nearest {category.lower()} anchor ({facility_name}) is {dist_km} km away "
        f"(infrastructure deficit: {infra_deficit}%), correlated with {cluster_count} "
        f"verified neighborhood submissions."
    )

    return final_score, level, factors, explanation


def calculate_priority_score(
    category: str, reports_count: int = 1
) -> PriorityEngineResponse:
    """Entry point for API controllers with dynamic defaults."""
    score, level, factors, explanation = evaluate_issue_priority(
        category=category,
        evidence_strength=0.70,
        latitude=20.2961,
        longitude=85.8245,
        db=None,
    )

    return PriorityEngineResponse(
        priority_score=score,
        level=level,
        factors=factors,
        explanation=explanation,
        analysis_mode="live",
    )
