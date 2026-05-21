"""
Financial Document Management API
===================================
Run (dev):   uvicorn main:app --reload
Run (prod):  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Docs:        http://localhost:8000/docs
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import Base, engine, SessionLocal, check_db_connection
from models import Role


# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if not settings.is_production else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Startup / shutdown ────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — environment=%s", settings.ENVIRONMENT)

    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified")

    # Seed default roles
    _seed_default_roles()

    yield  # ← app runs here

    logger.info("Shutting down")


def _seed_default_roles() -> None:
    """
    Insert the 4 default roles if they don't exist.
    Safe to call on every startup.
    """
    defaults = [
        {"name": "admin",   "description": "Full system access",             "permissions": "full_access"},
        {"name": "analyst", "description": "Upload and edit documents",       "permissions": "upload,edit,view"},
        {"name": "auditor", "description": "Review documents (read-only)",   "permissions": "view"},
        {"name": "client",  "description": "View company documents",         "permissions": "view"},
    ]
    db = SessionLocal()
    try:
        created = 0
        for r in defaults:
            if not db.query(Role).filter(Role.name == r["name"]).first():
                db.add(Role(**r))
                created += 1
        db.commit()
        if created:
            logger.info("Seeded %d default role(s)", created)
    except Exception as exc:
        db.rollback()
        logger.error("Role seeding failed: %s", exc)
    finally:
        db.close()


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Financial Document Management API",
    description="""
## Overview
Manage financial documents with role-based access control and AI-powered semantic search.

## Auth flow
1. `POST /auth/register` — create an account
2. `POST /auth/login`    — receive a JWT token
3. Click **Authorize** (top right) → paste the token → all protected routes unlock

## Default roles
| Role    | Permissions                        |
|---------|------------------------------------|
| admin   | full_access                        |
| analyst | upload, edit, view                 |
| auditor | view                               |
| client  | view                               |

Assign a role via `POST /users/assign-role` (admin only).
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ── CORS ──────────────────────────────────────────────────────────────────────
# Tighten allowed_origins in production to your actual frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{duration:.4f}s"
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred — please try again later"},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
from auth.routes      import router as auth_router
from documents.routes import router as docs_router
from roles.routes     import router as roles_router
from rag.routes       import router as rag_router

app.include_router(auth_router,  prefix="/auth")
app.include_router(docs_router,  prefix="/documents")
app.include_router(roles_router)
app.include_router(rag_router,   prefix="/rag")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"], summary="Basic liveness check")
def root():
    return {"status": "ok", "version": "1.0.0", "environment": settings.ENVIRONMENT}


@app.get("/health", tags=["Health"], summary="Detailed health check including DB connectivity")
def health():
    db_ok = check_db_connection()
    payload = {
        "status":      "healthy" if db_ok else "degraded",
        "database":    "ok" if db_ok else "unreachable",
        "environment": settings.ENVIRONMENT,
    }
    status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=payload, status_code=status_code)
