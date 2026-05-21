
import logging
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from config import settings

logger = logging.getLogger(__name__)


# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # validate connection before handing it to a route
    pool_size=10,             # maintained open connections
    max_overflow=20,          # extra connections allowed under burst load
    pool_timeout=30,          # seconds to wait for a connection from the pool
    pool_recycle=1800,        # recycle connections every 30 min (avoids stale TCP)
    echo=not settings.is_production,  # log SQL only in dev
)


# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── Declarative base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency injected into every route that needs the DB ───────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Yields a SQLAlchemy session scoped to the request lifetime.
    Rolls back on exception; always closes the session.

    Usage:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()  # auto-commit on clean exit so routes don't have to
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Health check helper ───────────────────────────────────────────────────────
def check_db_connection() -> bool:
    """Returns True if the database is reachable. Used by /health endpoint."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return False
