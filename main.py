# """JAN-NITI AI FastAPI Main Entry Point."""

# from contextlib import asynccontextmanager
# import os
# from pathlib import Path
# from dotenv import load_dotenv
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles

# # Load local environment variables (.env) before service initialization
# load_dotenv()

# from api import ai_router, government_router, issues_router

# from models.database import SessionLocal, init_db
# from services.issue_service import seed_demo_issues

# # Ensure persistent uploads folder exists for citizen photo evidence
# BASE_DIR = Path(__file__).resolve().parent.parent
# UPLOAD_DIR = BASE_DIR / "uploads"
# UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Initialize SQLite schema non-destructively
#     init_db()
#     db = SessionLocal()
#     try:
#         # Executes zero-data seeding (strictly no fake issues)
#         seed_demo_issues(db)
#     finally:
#         db.close()
#     yield


# app = FastAPI(
#     title="JAN-NITI AI API",
#     description=" API for citizen-driven constituency development insights.",
#     version="1.0.0",
#     lifespan=lifespan,
# )

# # Mount uploads directory so government portal can view uploaded citizen photo evidence
# app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# raw_origins = os.getenv(
#     "CORS_ORIGINS",
#     "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173",
# )
# allowed_origins = [
#     origin.strip() for origin in raw_origins.split(",") if origin.strip()
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=allowed_origins if allowed_origins else ["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(issues_router)
# app.include_router(government_router)
# app.include_router(ai_router)


# @app.get("/", tags=["Health"], summary="API Root")
# def root():
#     return {
#         "message": "JAN-NITI AI API is running",
#         "version": "1.0.0",
#     }


# @app.get("/health", tags=["Health"], summary="Health Check")
# def health():
#     return {"status": "healthy"}
"""JAN-NITI AI FastAPI Main Entry Point."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google import genai

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


# 1. FastAPI app initialize sabse pehle hona chahiye
app = FastAPI(
    title="JAN-NITI AI API",
    description=" API for citizen-driven constituency development insights.",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount uploads directory so government portal can view uploaded citizen photo evidence
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173",
)
allowed_origins = [
    origin.strip() for origin in raw_origins.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Routers include karein
app.include_router(issues_router)
app.include_router(government_router)
app.include_router(ai_router)


# 3. Ab app banne ke baad apne saare routes likhein
@app.get("/test-gemini", tags=["Health"], summary="Test Gemini Key")
def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return {
            "status": "error",
            "message": "GEMINI_API_KEY environment variable is missing!",
        }

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents="Say 'API is working perfectly!'"
        )
        return {
            "status": "success",
            "api_key_configured": True,
            "gemini_response": response.text.strip(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/", tags=["Health"], summary="API Root")
def root():
    return {
        "message": "JAN-NITI AI API is running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"], summary="Health Check")
def health():
    return {"status": "healthy"}
