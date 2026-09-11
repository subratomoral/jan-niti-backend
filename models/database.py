"""Database engine, session maker, base model, and safe table migrations."""

from pathlib import Path
import logging
import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_FILE = DB_DIR / "jan_niti.db"
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_FILE}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args=(
        {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    ),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency injection helper yielding a scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_sqlite_db_path() -> Path:
    """Extracts local SQLite file path safely from DATABASE_URL."""
    if DATABASE_URL.startswith("sqlite:///"):
        raw_path = DATABASE_URL.replace("sqlite:///", "")
        return Path(raw_path).resolve()
    return DEFAULT_DB_FILE


def _safe_sqlite_column_migration():
    """Safely inspects and adds analytical AI extension columns without dropping existing records."""
    if not DATABASE_URL.startswith("sqlite"):
        return

    db_path = _get_sqlite_db_path()
    if not db_path.exists():
        return

    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if table exists before inspecting columns
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='issues'"
        )
        if not cursor.fetchone():
            return

        cursor.execute("PRAGMA table_info(issues)")
        existing_cols = {row[1] for row in cursor.fetchall()}

        new_columns = {
            "ai_category": "VARCHAR(64)",
            "ai_intent": "VARCHAR(128)",
            "ai_summary": "TEXT",
            "ai_confidence": "FLOAT",
            "ai_observation": "TEXT",
            "priority_level": "VARCHAR(16)",
            "evidence_strength": "FLOAT",
            "analysis_mode": "VARCHAR(16) DEFAULT 'demo'",
            "analyzed_at": "DATETIME",
        }

        for col_name, col_type in new_columns.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE issues ADD COLUMN {col_name} {col_type}")

        conn.commit()
    except Exception as exc:
        logger.warning("SQLite column migration notice: %s", exc)
    finally:
        if conn:
            conn.close()


def init_db():
    """Idempotently creates all tables and runs non-destructive SQLite column extensions."""
    from models.issue import Issue  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _safe_sqlite_column_migration()
