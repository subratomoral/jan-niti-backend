"""API package routers."""

from backend.api.ai import router as ai_router
from backend.api.government import router as government_router
from backend.api.issues import router as issues_router

__all__ = ["issues_router", "government_router", "ai_router"]
