# """AI Service layer with Google GenAI SDK and Multimodal Signal Fusion."""

# from datetime import datetime, timezone
# import json
# import os
# import re
# from typing import Dict, Optional
# from sqlalchemy.orm import Session
# from google import genai
# from google.genai import types

# from models.issue import Issue
# from schemas.ai import (
#     CategoryType,
#     IssueAnalysisResponse,
#     MultimodalAnalysisRequest,
#     MultimodalAnalysisResponse,
#     MultimodalLocationSummary,
#     TextAnalysisResponse,
#     TextAnalysisSummary,
#     VisionAnalysisResponse,
# )
# from services.priority_service import (
#     compute_evidence_strength,
#     evaluate_issue_priority,
# )


# def _get_genai_client() -> Optional[genai.Client]:
#     """Dynamically reads the environment variable so late-loaded .env keys work seamlessly."""
#     key = os.getenv("GEMINI_API_KEY", "").strip()
#     return genai.Client(api_key=key) if key else None


# def safe_extract_json(raw_text: Optional[str]) -> dict:
#     """Safely extracts JSON from LLM outputs even if raw_text is None, contains markdown fences, or extra whitespace."""
#     if not raw_text or not str(raw_text).strip():
#         raise ValueError("Empty response text from LLM")

#     cleaned = str(raw_text).strip()
#     if cleaned.startswith("```"):
#         cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
#         cleaned = re.sub(r"\s*```$", "", cleaned)
#         cleaned = cleaned.strip()

#     match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
#     if match:
#         cleaned = match.group(1).strip()

#     return json.loads(cleaned)


# def analyze_issue_text_with_llm(raw_text: str) -> Optional[TextAnalysisResponse]:
#     """Uses Google Gemini to analyze citizen input in English, Hindi, or Hinglish."""
#     client = _get_genai_client()
#     if not client or not raw_text.strip():
#         return None

#     try:
#         prompt = f"""
#         You are an AI Civic Intelligence system for Indian governance.
#         Analyze this citizen grievance text (it may be in English, Hindi, or Hinglish):
#         "{raw_text}"

#         Respond ONLY with a valid JSON object matching this exact structure:
#         {{
#             "category": "Healthcare" | "Roads" | "Education" | "Water" | "Employment" | "Community Development" | "Other",
#             "intent": "Concise specific intent",
#             "summary": "1-2 sentence problem summary",
#             "priority_signal": "high" | "medium" | "low",
#             "confidence": 0.90,
#             "ai_observation": "Analytical observation regarding local development needs"
#         }}
#         """
#         response = client.models.generate_content(
#             model="gemini-3.6-flash",
#             contents=prompt,
#             config=types.GenerateContentConfig(response_mime_type="application/json"),
#         )

#         # Fix for line 81: response.text is safely accepted even if inferred as str | None
#         data = safe_extract_json(response.text or "")

#         return TextAnalysisResponse(
#             category=data.get("category", "Other"),
#             intent=data.get("intent", "General Civic Issue"),
#             summary=data.get("summary", raw_text[:140]),
#             priority_signal=data.get("priority_signal", "medium"),
#             confidence=float(data.get("confidence", 0.90)),
#             ai_observation=data.get("ai_observation", "Issue logged via AI pipeline."),
#             analysis_mode="live",
#         )
#     except Exception as e:
#         print(f"Gemini LLM Text Analysis Fallback: {e}")
#         return None


# def analyze_issue_text(raw_text: Optional[str] = "") -> TextAnalysisResponse:
#     """Primary entry point: safely handles None/str, tries Gemini LLM first, and falls back to deterministic heuristics."""
#     clean_text = str(raw_text or "").strip()
#     llm_res = analyze_issue_text_with_llm(clean_text)
#     if llm_res:
#         return llm_res

#     # Heuristic Fallback
#     cleaned = clean_text.lower()
#     cat = "Other"
#     intent = "General Civic Issue"
#     prio = "medium"

#     if any(
#         w in cleaned
#         for w in [
#             "hospital",
#             "doctor",
#             "aspatal",
#             "dawai",
#             "health",
#             "ambulance",
#             "clinic",
#             "dawa",
#         ]
#     ):
#         cat, intent, prio = "Healthcare", "Healthcare Access", "high"
#     elif any(
#         w in cleaned
#         for w in ["road", "sadak", "pothole", "gaddha", "bridge", "traffic", "pul"]
#     ):
#         cat, intent, prio = "Roads", "Road Infrastructure", "high"
#     elif any(
#         w in cleaned
#         for w in ["water", "pani", "paani", "pipeline", "borewell", "tap", "nal", "jal"]
#     ):
#         cat, intent, prio = "Water", "Water Supply", "high"
#     elif any(
#         w in cleaned
#         for w in ["school", "teacher", "education", "padhai", "vidyalaya", "shiksha"]
#     ):
#         cat, intent, prio = "Education", "Education Facility", "medium"
#     elif any(
#         w in cleaned
#         for w in ["job", "naukri", "rojgar", "work", "unemployment", "skill"]
#     ):
#         cat, intent, prio = "Employment", "Livelihood & Skills", "medium"

#     return TextAnalysisResponse(
#         category=cat,  # type: ignore
#         intent=intent,
#         summary=clean_text[:140] if clean_text else "Civic issue submitted.",
#         priority_signal=prio,  # type: ignore
#         confidence=0.85,
#         ai_observation=f"{cat} concern identified for localized review.",
#         analysis_mode="demo",
#     )


# def process_multimodal_fusion(
#     req: MultimodalAnalysisRequest,
# ) -> MultimodalAnalysisResponse:
#     """Fuses Text, Voice Transcript, Vision, and Location into an explainable unified context."""
#     has_text = bool(req.text and req.text.strip())
#     has_voice = bool(req.voice_transcript and req.voice_transcript.strip())
#     has_vision = bool(req.vision_category and req.vision_category != "Other")
#     has_location = bool(req.latitude is not None and req.longitude is not None)

#     # Fix for line 165: Guarantees primary_text is strictly a str (never None)
#     if has_text and req.text:
#         primary_text: str = req.text
#     elif has_voice and req.voice_transcript:
#         primary_text = req.voice_transcript
#     else:
#         primary_text = ""

#     text_res = analyze_issue_text(primary_text)

#     final_category: CategoryType = text_res.category
#     final_intent = text_res.intent
#     consistency_flag = "single_source"
#     consistency_message = None

#     if has_vision and (has_text or has_voice):
#         if req.vision_category == text_res.category:
#             consistency_flag = "consistent"
#             consistency_message = f"Multimodal Signal Match: Text and image evidence both confirm {final_category} conditions."
#         else:
#             consistency_flag = "conflict"
#             consistency_message = (
#                 f"⚠️ Multimodal Discrepancy: Written concern describes '{text_res.category}', "
#                 f"while attached photo depicts '{req.vision_category}'. Field check required."
#             )
#     elif (has_text and has_voice) or (has_vision and not has_text):
#         if has_vision and not has_text:
#             final_category = req.vision_category  # type: ignore
#             final_intent = "Verified Visual Evidence Report"
#         consistency_flag = "consistent"

#     evidence_score = compute_evidence_strength(
#         has_text=has_text,
#         has_audio=has_voice,
#         has_image=has_vision,
#         has_location=has_location,
#         image_evidence_signal=req.vision_evidence_signal,
#     )

#     if consistency_flag == "conflict":
#         evidence_score = round(max(0.20, evidence_score - 0.20), 2)

#     prio_score, _, _, _ = evaluate_issue_priority(
#         category=final_category,
#         evidence_strength=evidence_score,
#         latitude=req.latitude,
#         longitude=req.longitude,
#     )
#     priority_weight = round(prio_score / 100.0, 2)

#     if consistency_flag == "consistent" and has_vision:
#         ai_obs = f"Multimodal verified: Submitted description and visual evidence confirm localized {final_category.lower()} priority."
#     elif consistency_flag == "conflict":
#         ai_obs = f"Multimodal conflict flagged: Text highlights '{text_res.category}' while photo indicates '{req.vision_category}'. Administrative inspection required."
#     else:
#         ai_obs = text_res.ai_observation

#     text_summary = None
#     if has_text or has_voice:
#         text_summary = TextAnalysisSummary(
#             category=text_res.category,
#             intent=text_res.intent,
#             summary=text_res.summary,
#             confidence=text_res.confidence,
#         )

#     vision_summary = None
#     if req.vision_category:
#         vision_summary = VisionAnalysisResponse(
#             possible_category=req.vision_category,
#             observations=req.vision_observations or ["Civic evidence photo verified."],
#             evidence_signal=req.vision_evidence_signal or 0.75,
#             confidence=0.88,
#             analysis_mode="live" if _get_genai_client() else "demo",
#         )

#     return MultimodalAnalysisResponse(
#         category=final_category,
#         intent=final_intent,
#         text_analysis=text_summary,
#         speech_analysis=None,
#         vision_analysis=vision_summary,
#         location=MultimodalLocationSummary(
#             available=has_location,
#             latitude=req.latitude,
#             longitude=req.longitude,
#             location_name=req.location_name,
#         ),
#         evidence_signal=evidence_score,
#         priority_signal=priority_weight,
#         consistency_flag=consistency_flag,  # type: ignore
#         consistency_message=consistency_message,
#         ai_observation=ai_obs,
#         analysis_mode=text_res.analysis_mode,
#     )


# def analyze_and_persist_issue(db: Session, issue: Issue) -> IssueAnalysisResponse:
#     """Executes AI understanding and updates SQLite record with type-safe attribute handling."""
#     text_content: str = str(getattr(issue, "text", "") or "")
#     understanding = analyze_issue_text(text_content)

#     input_type_val: str = str(getattr(issue, "input_type", "") or "")
#     audio_path_val = getattr(issue, "audio_path", None)
#     image_path_val = getattr(issue, "image_path", None)
#     lat_val = getattr(issue, "latitude", None)
#     lng_val = getattr(issue, "longitude", None)

#     ev_strength = compute_evidence_strength(
#         has_text=bool(text_content.strip()),
#         has_audio=bool(audio_path_val or ("voice" in input_type_val)),
#         has_image=bool(image_path_val or ("photo" in input_type_val)),
#         has_location=bool(lat_val is not None and lng_val is not None),
#     )

#     clean_lat: Optional[float] = float(lat_val) if lat_val is not None else None
#     clean_lng: Optional[float] = float(lng_val) if lng_val is not None else None

#     score, level, factor_breakdown, _ = evaluate_issue_priority(
#         category=understanding.category,
#         evidence_strength=ev_strength,
#         latitude=clean_lat,
#         longitude=clean_lng,
#         db=db,
#     )
#     now_utc = datetime.now(timezone.utc)

#     setattr(issue, "ai_category", str(understanding.category))
#     setattr(issue, "ai_intent", str(understanding.intent))
#     setattr(issue, "ai_summary", str(understanding.summary))
#     setattr(issue, "ai_confidence", float(understanding.confidence))
#     setattr(issue, "ai_observation", str(understanding.ai_observation))
#     setattr(issue, "priority_score", float(score))
#     setattr(issue, "priority_level", str(level))
#     setattr(issue, "evidence_strength", float(ev_strength))
#     setattr(issue, "analysis_mode", str(understanding.analysis_mode))
#     setattr(issue, "analyzed_at", now_utc)
#     setattr(issue, "status", "analyzed")

#     db.commit()
#     db.refresh(issue)

#     issue_id_val: int = int(getattr(issue, "id", 0))

#     return IssueAnalysisResponse(
#         issue_id=issue_id_val,
#         category=understanding.category,
#         intent=understanding.intent,
#         summary=understanding.summary,
#         confidence=understanding.confidence,
#         priority_signal=understanding.priority_signal,
#         priority_score=int(score),
#         priority_level=level,
#         factor_breakdown=factor_breakdown,
#         evidence_strength=ev_strength,
#         ai_observation=understanding.ai_observation,
#         recommended_verification="Field verification recommended",
#         analysis_mode=understanding.analysis_mode,
#         analyzed_at=now_utc,
#     )
"""AI Service layer with Google GenAI SDK and Multimodal Signal Fusion."""

from datetime import datetime, timezone
import json
import os
import re
from typing import Dict, Optional
from sqlalchemy.orm import Session
from google import genai
from google.genai import types

from models.issue import Issue
from schemas.ai import (
    CategoryType,
    IssueAnalysisResponse,
    MultimodalAnalysisRequest,
    MultimodalAnalysisResponse,
    MultimodalLocationSummary,
    TextAnalysisResponse,
    TextAnalysisSummary,
    VisionAnalysisResponse,
)
from services.priority_service import (
    compute_evidence_strength,
    evaluate_issue_priority,
)


def _get_genai_client() -> Optional[genai.Client]:
    """Dynamically reads the environment variable so late-loaded .env keys work seamlessly."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return genai.Client(api_key=key) if key else None


def safe_extract_json(raw_text: Optional[str]) -> dict:
    """Safely extracts JSON from LLM outputs even if raw_text is None, contains markdown fences, or extra whitespace."""
    if not raw_text or not str(raw_text).strip():
        raise ValueError("Empty response text from LLM")

    cleaned = str(raw_text).strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()

    return json.loads(cleaned)


def analyze_issue_text_with_llm(raw_text: str) -> Optional[TextAnalysisResponse]:
    """Uses Google Gemini to analyze citizen input in English, Hindi, or Hinglish with strict noise/validity checks."""
    client = _get_genai_client()
    if not client or not raw_text.strip():
        return None

    try:
        prompt = f"""
        You are a strict AI Civic Intelligence forensic system for Indian governance.
        Analyze this citizen grievance text input (English, Hindi, or Hinglish):
        "{raw_text}"

        1. Determine if this text describes a real, actionable public civic issue (e.g., roads, water, healthcare, education, sanitation).
        2. If the text is gibberish, random keypresses, spam, casual greetings ("hi", "hello"), or completely non-civic noise, set "is_valid_civic_issue" to false, category to "Other", priority_signal to "low", confidence to 0.10, and provide a clear observation explaining that no valid civic concern was found.
        3. If valid, assign the correct category, intent, summary, priority_signal ("high", "medium", "low"), confidence, and a professional civic observation.

        Respond ONLY with a valid JSON object matching this exact structure:
        {{
            "is_valid_civic_issue": true,
            "category": "Healthcare" | "Roads" | "Education" | "Water" | "Employment" | "Community Development" | "Other",
            "intent": "Concise specific intent",
            "summary": "1-2 sentence problem summary",
            "priority_signal": "high" | "medium" | "low",
            "confidence": 0.90,
            "ai_observation": "Analytical observation regarding local development needs"
        }}
        """
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

        data = safe_extract_json(response.text or "")
        is_valid = bool(data.get("is_valid_civic_issue", True))

        if not is_valid:
            return TextAnalysisResponse(
                category="Other",
                intent="Invalid or Non-Civic Input",
                summary="The input appears to be noise or an accidental keypress sequence. No actionable civic concern found.",
                priority_signal="low",
                confidence=0.15,
                ai_observation="Input filtered as non-civic noise or spam.",
                analysis_mode="live",
            )

        return TextAnalysisResponse(
            category=data.get("category", "Other"),
            intent=data.get("intent", "General Civic Issue"),
            summary=data.get("summary", raw_text[:140]),
            priority_signal=data.get("priority_signal", "medium"),
            confidence=float(data.get("confidence", 0.90)),
            ai_observation=data.get("ai_observation", "Issue logged via AI pipeline."),
            analysis_mode="live",
        )
    except Exception as e:
        print(f"Gemini LLM Text Analysis Fallback: {e}")
        return None


def analyze_issue_text(raw_text: Optional[str] = "") -> TextAnalysisResponse:
    """Primary entry point: safely handles None/str, tries Gemini LLM first, and falls back to deterministic heuristics."""
    clean_text = str(raw_text or "").strip()

    # Simple check for obvious noise / random strings
    if len(clean_text) < 3 or clean_text.lower() in [
        "hi",
        "hello",
        "test",
        "asdf",
        ".",
    ]:
        return TextAnalysisResponse(
            category="Other",
            intent="Invalid Input",
            summary="The input appears to be noise or an accidental keypress sequence. No actionable civic concern could be extracted.",
            priority_signal="low",
            confidence=0.10,
            ai_observation="Input lacks substantive civic grievance details.",
            analysis_mode="demo",
        )

    llm_res = analyze_issue_text_with_llm(clean_text)
    if llm_res:
        return llm_res

    # Heuristic Fallback
    cleaned = clean_text.lower()
    cat = "Other"
    intent = "General Civic Issue"
    prio = "medium"

    if any(
        w in cleaned
        for w in [
            "hospital",
            "doctor",
            "aspatal",
            "dawai",
            "health",
            "ambulance",
            "clinic",
            "dawa",
        ]
    ):
        cat, intent, prio = "Healthcare", "Healthcare Access", "high"
    elif any(
        w in cleaned
        for w in ["road", "sadak", "pothole", "gaddha", "bridge", "traffic", "pul"]
    ):
        cat, intent, prio = "Roads", "Road Infrastructure", "high"
    elif any(
        w in cleaned
        for w in ["water", "pani", "paani", "pipeline", "borewell", "tap", "nal", "jal"]
    ):
        cat, intent, prio = "Water", "Water Supply", "high"
    elif any(
        w in cleaned
        for w in ["school", "teacher", "education", "padhai", "vidyalaya", "shiksha"]
    ):
        cat, intent, prio = "Education", "Education Facility", "medium"
    elif any(
        w in cleaned
        for w in ["job", "naukri", "rojgar", "work", "unemployment", "skill"]
    ):
        cat, intent, prio = "Employment", "Livelihood & Skills", "medium"

    return TextAnalysisResponse(
        category=cat,  # type: ignore
        intent=intent,
        summary=clean_text[:140] if clean_text else "Civic issue submitted.",
        priority_signal=prio,  # type: ignore
        confidence=0.85,
        ai_observation=f"{cat} concern identified for localized review.",
        analysis_mode="demo",
    )


def process_multimodal_fusion(
    req: MultimodalAnalysisRequest,
) -> MultimodalAnalysisResponse:
    """Fuses Text, Voice Transcript, Vision, and Location into an explainable unified context with strict discrepancy penalty."""
    has_text = bool(req.text and req.text.strip())
    has_voice = bool(req.voice_transcript and req.voice_transcript.strip())
    has_vision = bool(req.vision_category and req.vision_category != "Other")
    has_location = bool(req.latitude is not None and req.longitude is not None)

    if has_text and req.text:
        primary_text: str = req.text
    elif has_voice and req.voice_transcript:
        primary_text = req.voice_transcript
    else:
        primary_text = ""

    text_res = analyze_issue_text(primary_text)

    final_category: CategoryType = text_res.category
    final_intent = text_res.intent
    consistency_flag = "single_source"
    consistency_message = None

    # Handle Vision + Text cross-validation
    if has_vision and (has_text or has_voice):
        if req.vision_category == text_res.category:
            consistency_flag = "consistent"
            consistency_message = f"Multimodal Signal Match: Text and image evidence both confirm {final_category} conditions."
        else:
            consistency_flag = "conflict"
            consistency_message = (
                f"⚠️ Multimodal Discrepancy: Written concern describes '{text_res.category}', "
                f"while attached photo depicts '{req.vision_category}'. Field check required."
            )
    elif (has_text and has_voice) or (has_vision and not has_text):
        if has_vision and not has_text:
            final_category = req.vision_category  # type: ignore
            final_intent = "Verified Visual Evidence Report"
        consistency_flag = "consistent"

    evidence_score = compute_evidence_strength(
        has_text=has_text,
        has_audio=has_voice,
        has_image=has_vision,
        has_location=has_location,
        image_evidence_signal=req.vision_evidence_signal,
    )

    # Apply severe penalty if vision evidence indicates a healthy/good condition (false report or healthy road)
    if req.vision_evidence_signal is not None and req.vision_evidence_signal < 0.35:
        evidence_score = round(max(0.10, evidence_score * 0.4), 2)
        consistency_flag = "conflict"
        consistency_message = "⚠️ Visual inspection detected healthy or non-defective infrastructure. Priority downgraded."

    if consistency_flag == "conflict":
        evidence_score = round(max(0.15, evidence_score - 0.25), 2)

    prio_score, _, _, _ = evaluate_issue_priority(
        category=final_category,
        evidence_strength=evidence_score,
        latitude=req.latitude,
        longitude=req.longitude,
    )
    priority_weight = round(prio_score / 100.0, 2)

    if consistency_flag == "consistent" and has_vision:
        ai_obs = f"Multimodal verified: Submitted description and visual evidence confirm localized {final_category.lower()} priority."
    elif consistency_flag == "conflict":
        ai_obs = f"Multimodal conflict/discrepancy flagged. Administrative inspection required."
    else:
        ai_obs = text_res.ai_observation

    text_summary = None
    if has_text or has_voice:
        text_summary = TextAnalysisSummary(
            category=text_res.category,
            intent=text_res.intent,
            summary=text_res.summary,
            confidence=text_res.confidence,
        )

    vision_summary = None
    if req.vision_category:
        vision_summary = VisionAnalysisResponse(
            possible_category=req.vision_category,
            observations=req.vision_observations or ["Civic evidence photo verified."],
            evidence_signal=req.vision_evidence_signal or 0.75,
            confidence=0.88,
            analysis_mode="live" if _get_genai_client() else "demo",
        )

    return MultimodalAnalysisResponse(
        category=final_category,
        intent=final_intent,
        text_analysis=text_summary,
        speech_analysis=None,
        vision_analysis=vision_summary,
        location=MultimodalLocationSummary(
            available=has_location,
            latitude=req.latitude,
            longitude=req.longitude,
            location_name=req.location_name,
        ),
        evidence_signal=evidence_score,
        priority_signal=priority_weight,
        consistency_flag=consistency_flag,  # type: ignore
        consistency_message=consistency_message,
        ai_observation=ai_obs,
        analysis_mode=text_res.analysis_mode,
    )


def analyze_and_persist_issue(db: Session, issue: Issue) -> IssueAnalysisResponse:
    """Executes AI understanding and updates SQLite record with type-safe attribute handling."""
    text_content: str = str(getattr(issue, "text", "") or "")
    understanding = analyze_issue_text(text_content)

    input_type_val: str = str(getattr(issue, "input_type", "") or "")
    audio_path_val = getattr(issue, "audio_path", None)
    image_path_val = getattr(issue, "image_path", None)
    lat_val = getattr(issue, "latitude", None)
    lng_val = getattr(issue, "longitude", None)

    ev_strength = compute_evidence_strength(
        has_text=bool(text_content.strip()),
        has_audio=bool(audio_path_val or ("voice" in input_type_val)),
        has_image=bool(image_path_val or ("photo" in input_type_val)),
        has_location=bool(lat_val is not None and lng_val is not None),
    )

    clean_lat: Optional[float] = float(lat_val) if lat_val is not None else None
    clean_lng: Optional[float] = float(lng_val) if lng_val is not None else None

    score, level, factor_breakdown, _ = evaluate_issue_priority(
        category=understanding.category,
        evidence_strength=ev_strength,
        latitude=clean_lat,
        longitude=clean_lng,
        db=db,
    )
    now_utc = datetime.now(timezone.utc)

    setattr(issue, "ai_category", str(understanding.category))
    setattr(issue, "ai_intent", str(understanding.intent))
    setattr(issue, "ai_summary", str(understanding.summary))
    setattr(issue, "ai_confidence", float(understanding.confidence))
    setattr(issue, "ai_observation", str(understanding.ai_observation))
    setattr(issue, "priority_score", float(score))
    setattr(issue, "priority_level", str(level))
    setattr(issue, "evidence_strength", float(ev_strength))
    setattr(issue, "analysis_mode", str(understanding.analysis_mode))
    setattr(issue, "analyzed_at", now_utc)
    setattr(issue, "status", "analyzed")

    db.commit()
    db.refresh(issue)

    issue_id_val: int = int(getattr(issue, "id", 0))

    return IssueAnalysisResponse(
        issue_id=issue_id_val,
        category=understanding.category,
        intent=understanding.intent,
        summary=understanding.summary,
        confidence=understanding.confidence,
        priority_signal=understanding.priority_signal,
        priority_score=int(score),
        priority_level=level,
        factor_breakdown=factor_breakdown,
        evidence_strength=ev_strength,
        ai_observation=understanding.ai_observation,
        recommended_verification="Field verification recommended",
        analysis_mode=understanding.analysis_mode,
        analyzed_at=now_utc,
    )
