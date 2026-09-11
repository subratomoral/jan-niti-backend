"""API package routers."""

from api.ai import router as ai_router
from api.government import router as government_router
from api.issues import router as issues_router

__all__ = ["issues_router", "government_router", "ai_router"]
