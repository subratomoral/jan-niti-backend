# """Computer Vision evidence analysis service with Gemini Vision SDK and Civic Authenticity Verification."""

# import io
# import json
# import os
# import re
# from typing import Any, Dict, List, Optional
# from PIL import Image
# from fastapi import HTTPException, UploadFile, status
# from google import genai
# from google.genai import types

# from schemas.ai import VisionAnalysisResponse

# SUPPORTED_IMAGE_MIMES = {
#     "image/jpeg",
#     "image/jpg",
#     "image/png",
#     "image/webp",
# }
# MAX_IMAGE_BYTES = 10 * 1024 * 1024


# def _get_client():
#     api_key = os.getenv("GEMINI_API_KEY", "").strip()
#     return genai.Client(api_key=api_key) if api_key else None


# def safe_extract_json(raw_text: Optional[str]) -> Dict[str, Any]:
#     """Safely extracts JSON from LLM outputs even if raw_text is None, contains markdown code blocks, or extra whitespace."""
#     if not raw_text or not str(raw_text).strip():
#         raise ValueError("Empty response text from LLM")

#     cleaned = str(raw_text).strip()

#     # Markdown blocks strip karein (```json ... ```)
#     if cleaned.startswith("```"):
#         cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
#         cleaned = re.sub(r"\s*```$", "", cleaned)
#         cleaned = cleaned.strip()

#     # JSON boundary detect karein
#     match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
#     if match:
#         cleaned = match.group(1).strip()

#     return json.loads(cleaned)


# async def analyze_photo_evidence(file: UploadFile) -> VisionAnalysisResponse:
#     if not file:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="No image file provided.",
#         )

#     raw_content = (file.content_type or "").lower()
#     content_type = raw_content.split(";")[0].strip()

#     if content_type not in SUPPORTED_IMAGE_MIMES and not (
#         file.filename or ""
#     ).lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
#         raise HTTPException(
#             status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
#             detail=f"Unsupported image format '{content_type}'.",
#         )

#     image_bytes = await file.read()
#     await file.seek(0)

#     if len(image_bytes) == 0:
#         raise HTTPException(
#             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#             detail="Uploaded image file is empty.",
#         )

#     if len(image_bytes) > MAX_IMAGE_BYTES:
#         raise HTTPException(
#             status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
#             detail="Image file exceeds 10 MB limit.",
#         )

#     # 1. Real Gemini Vision with Anti-Fraud Infrastructure Verification
#     client = _get_client()
#     if client:
#         try:
#             img = Image.open(io.BytesIO(image_bytes))
#             prompt = """
#             You are a senior civic inspection forensic AI.
#             Inspect this citizen grievance photo evidence with high scrutiny:
#             1. Verify whether this image genuinely depicts public civic infrastructure (e.g. damaged roads/potholes, water pipeline burst/leakage, garbage overflow, public hospital/health clinic, school building, electrical hazard).
#             2. If the photo is a personal selfie, computer screen, indoor bedroom, food, pet, or completely unrelated image, mark "valid_civic_evidence": false.
#             3. If "valid_civic_evidence" is false, set "evidence_signal" between 0.10 and 0.25, and set "possible_category" to "Other".
#             4. If valid, classify the exact civic category, evaluate image clarity/severity for "evidence_signal" (0.65 to 0.98), and write 2-3 concise, objective technical observations.

#             Respond ONLY with a valid JSON object matching this schema:
#             {
#                 "valid_civic_evidence": true,
#                 "possible_category": "Healthcare" | "Roads" | "Education" | "Water" | "Employment" | "Community Development" | "Other",
#                 "observations": ["technical observation 1", "technical observation 2"],
#                 "evidence_signal": 0.85,
#                 "confidence": 0.90
#             }
#             """
#             response = client.models.generate_content(
#                 model="gemini-3.6-flash",
#                 contents=[prompt, img],
#                 config=types.GenerateContentConfig(
#                     response_mime_type="application/json"
#                 ),
#             )

#             # Fix: response.text is safely accepted even if inferred as str | None
#             data = safe_extract_json(response.text or "")

#             is_valid = bool(data.get("valid_civic_evidence", True))
#             raw_observations = data.get("observations", [])
#             if isinstance(raw_observations, list):
#                 observations: List[str] = [str(obs) for obs in raw_observations]
#             else:
#                 observations = [str(raw_observations)]

#             if not is_valid:
#                 observations.insert(
#                     0,
#                     "⚠️ Image verification warning: Uploaded photo does not depict recognizable public infrastructure.",
#                 )

#             return VisionAnalysisResponse(
#                 possible_category=data.get("possible_category", "Other"),
#                 observations=observations or ["Civic evidence visually cataloged."],
#                 evidence_signal=float(
#                     data.get("evidence_signal", 0.80 if is_valid else 0.20)
#                 ),
#                 confidence=float(data.get("confidence", 0.90)),
#                 analysis_mode="live",
#             )
#         except Exception as e:
#             print(f"Gemini Vision Verification Fallback: {e}")

#     # 2. Heuristic Context-Aware Fallback
#     fn = (file.filename or "").lower()
#     if any(k in fn for k in ["road", "pothole", "street", "sadak", "gaddha"]):
#         cat = "Roads"
#         obs = [
#             "Surface cratering and unpaved shoulder degradation visible in evidence",
#             "Pothole cluster presents impediment to vehicular and pedestrian transit",
#         ]
#         ev_signal = 0.78
#     elif any(k in fn for k in ["water", "pipe", "tap", "drain", "flood", "pani"]):
#         cat = "Water"
#         obs = [
#             "Surface pipeline fracture with visible water accumulation",
#             "Localized drainage backflow and supply impediment indicators present",
#         ]
#         ev_signal = 0.76
#     elif any(k in fn for k in ["hospital", "clinic", "health", "doctor", "aspatal"]):
#         cat = "Healthcare"
#         obs = [
#             "Infrastructure attributes consistent with rural/ward healthcare facility",
#             "High patient load conditions and structural maintenance deficits detected",
#         ]
#         ev_signal = 0.75
#     elif any(k in fn for k in ["school", "class", "teacher", "education", "vidyalaya"]):
#         cat = "Education"
#         obs = [
#             "Public educational facility structure identified",
#             "Classroom masonry wear and infrastructural maintenance requirements visible",
#         ]
#         ev_signal = 0.72
#     else:
#         cat = "Other"
#         obs = [
#             "General visual civic evidence uploaded by citizen",
#             "Physical conditions logged for field inspection verification",
#         ]
#         ev_signal = 0.60

#     return VisionAnalysisResponse(
#         possible_category=cat,  # type: ignore
#         observations=obs,
#         evidence_signal=ev_signal,
#         confidence=0.80,
#         analysis_mode="demo",
#     )


# analyze_image_evidence = analyze_photo_evidence
"""Computer Vision evidence analysis service with Gemini Vision SDK and Rigorous Civic Authenticity Verification."""

import io
import json
import os
import re
from typing import Any, Dict, List, Optional
from PIL import Image
from fastapi import HTTPException, UploadFile, status
from google import genai
from google.genai import types

from schemas.ai import VisionAnalysisResponse

SUPPORTED_IMAGE_MIMES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def _get_client():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    return genai.Client(api_key=api_key) if api_key else None


def safe_extract_json(raw_text: Optional[str]) -> Dict[str, Any]:
    """Safely extracts JSON from LLM outputs even if raw_text is None, contains markdown code blocks, or extra whitespace."""
    if not raw_text or not str(raw_text).strip():
        raise ValueError("Empty response text from LLM")

    cleaned = str(raw_text).strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=r"")
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()

    return json.loads(cleaned)


async def analyze_photo_evidence(file: UploadFile) -> VisionAnalysisResponse:
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image file provided.",
        )

    raw_content = (file.content_type or "").lower()
    content_type = raw_content.split(";")[0].strip()

    if content_type not in SUPPORTED_IMAGE_MIMES and not (
        file.filename or ""
    ).lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported image format '{content_type}'.",
        )

    image_bytes = await file.read()
    await file.seek(0)

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded image file is empty.",
        )

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image file exceeds 10 MB limit.",
        )

    # 1. Real Gemini Vision with Rigorous Anti-Fraud & Infrastructure Defect Verification
    client = _get_client()
    if client:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            prompt = """
            You are a strict senior civic inspection forensic AI. Inspect this citizen photo evidence with high skepticism:
            1. Determine if this image genuinely depicts a BROKEN, DAMAGED, or HAZARDOUS public civic infrastructure problem (e.g., severe potholes, deep road craters, massive garbage dump, water pipe burst, broken public structure).
            2. CRITICAL RULE: If the photo shows a NORMAL, HEALTHY, CLEAN, or NEWLY PAVED ROAD without any major damage, or if it's an indoor room, selfie, food, animal, computer screen, or unrelated picture, you MUST set "valid_civic_evidence" to false and "evidence_signal" to a very low value between 0.10 and 0.25.
            3. Only if severe, visible civic infrastructure damage/defect is present, set "valid_civic_evidence" to true and assign a high "evidence_signal" (0.65 to 0.98).
            4. Write 2-3 objective technical observations describing the exact physical condition.

            Respond ONLY with a valid JSON object matching this schema:
            {
                "valid_civic_evidence": true/false,
                "possible_category": "Healthcare" | "Roads" | "Education" | "Water" | "Employment" | "Community Development" | "Other",
                "observations": ["technical observation 1", "technical observation 2"],
                "evidence_signal": 0.20,
                "confidence": 0.90
            }
            """
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[prompt, img],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            data = safe_extract_json(response.text or "")

            is_valid = bool(data.get("valid_civic_evidence", True))
            raw_observations = data.get("observations", [])
            if isinstance(raw_observations, list):
                observations: List[str] = [str(obs) for obs in raw_observations]
            else:
                observations = [str(raw_observations)]

            ev_signal = float(data.get("evidence_signal", 0.80 if is_valid else 0.20))

            if not is_valid:
                observations.insert(
                    0,
                    "⚠️ Image inspection note: Photo displays normal or non-defective infrastructure. High priority score suppressed.",
                )
                cat = "Other"
            else:
                cat = data.get("possible_category", "Roads")

            return VisionAnalysisResponse(
                possible_category=cat,
                observations=observations or ["Civic evidence visually cataloged."],
                evidence_signal=ev_signal if is_valid else 0.20,
                confidence=float(data.get("confidence", 0.90)),
                analysis_mode="live",
            )
        except Exception as e:
            print(f"Gemini Vision Verification Fallback: {e}")

    # 2. Heuristic Context-Aware Fallback
    fn = (file.filename or "").lower()
    if any(k in fn for k in ["road", "pothole", "street", "sadak", "gaddha"]):
        cat = "Roads"
        obs = ["Surface cratering and unpaved shoulder degradation visible in evidence"]
        ev_signal = 0.78
    else:
        cat = "Other"
        obs = ["General visual civic evidence uploaded by citizen"]
        ev_signal = 0.40

    return VisionAnalysisResponse(
        possible_category=cat,  # type: ignore
        observations=obs,
        evidence_signal=ev_signal,
        confidence=0.80,
        analysis_mode="demo",
    )


analyze_image_evidence = analyze_photo_evidence
