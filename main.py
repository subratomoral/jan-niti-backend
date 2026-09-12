"""JAN-NITI AI FastAPI Main Entry Point."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load local environment variables (.env) before service initialization
load_dotenv()

from api import ai_router, government_router, issues_router

from models.database import SessionLocal, init_db
from services.issue_service import seed_demo_issues

# Ensure persistent uploads folder exists for citizen photo evidence
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema non-destructively
    init_db()
    db = SessionLocal()
    try:
        # Executes zero-data seeding (strictly no fake issues)
        seed_demo_issues(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="JAN-NITI AI API",
    description="API for citizen-driven constituency development insights.",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount uploads directory so government portal can view uploaded citizen photo evidence
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Allow all origins to prevent any CORS preflight or 400 errors from Netlify or custom domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(issues_router)
app.include_router(government_router)
app.include_router(ai_router)


@app.get("/", tags=["Health"], summary="API Root")
def root():
    return {
        "message": "JAN-NITI AI API is running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"], summary="Health Check")
def health():
    return {"status": "healthy"}
