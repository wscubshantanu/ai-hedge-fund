"""
AETHER Capital — FastAPI Application Entry Point
Production-grade middleware stack, structured logging, and route registration.
"""
import sys
import uuid
import time
import logging
import collections
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.app.config import settings
from backend.app.database import init_db

# Windows UTF-8 fix
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Structured Logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("aether.capital")


# ── Application Lifecycle ────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on startup/shutdown."""
    logger.info("═" * 60)
    logger.info("  AETHER CAPITAL v%s — Starting Up", settings.VERSION)
    logger.info("  Database: %s", settings.DATABASE_URL[:50] + "..." if len(settings.DATABASE_URL) > 50 else settings.DATABASE_URL)
    logger.info("  Demo Mode: %s", settings.DEMO_MODE)
    logger.info("  OpenAI Key: %s", "CONFIGURED" if settings.has_openai_key else "NOT SET (using deterministic fallback)")
    logger.info("═" * 60)

    # Initialize database tables
    init_db()
    logger.info("Database tables initialized")

    # Seed default admin user if empty
    _seed_default_user()

    yield
    logger.info("AETHER CAPITAL shutting down")


def _seed_default_user():
    """Create a default admin user if the database is empty.
    
    Uses raw bcrypt (not passlib) to avoid the bcrypt.__about__ passlib
    compatibility error that occurs with newer bcrypt versions.
    """
    import bcrypt as _bcrypt
    from backend.app.database import SessionLocal
    from backend.app.models.user import User

    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            pw_bytes = "quant2026".encode()[:72]
            hashed = _bcrypt.hashpw(pw_bytes, _bcrypt.gensalt(rounds=12)).decode()
            admin = User(
                email="analyst@aether.fund",
                username="shantanu",
                hashed_password=hashed,
                full_name="Shantanu Kalhapure (Lead Quantitative Strategist)",
                role="admin",
            )
            db.add(admin)

            guest_pw = "demo1234".encode()[:72]
            guest_hashed = _bcrypt.hashpw(guest_pw, _bcrypt.gensalt(rounds=12)).decode()
            guest = User(
                email="guest@aether.fund",
                username="guest",
                hashed_password=guest_hashed,
                full_name="Institutional Guest",
                role="viewer",
            )
            db.add(guest)
            db.commit()
            logger.info("Seeded default users: analyst@aether.fund, guest@aether.fund")
    except Exception as e:
        logger.warning("User seeding skipped: %s", e)
        db.rollback()
    finally:
        db.close()



# ── App Factory ──────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "AI-Powered Quantitative Investment Research, Portfolio Optimization, "
        "Risk Management & Paper Trading Platform"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NOTE: Middleware classes are defined below and registered after
# their class bodies — see _register_middleware() call below.

# ── Middleware: Rate Limiting + Security Headers ─────────────────
# We use BaseHTTPMiddleware (not @app.middleware) because StreamingResponse
# headers must be set BEFORE the response body is streamed — the decorator
# form calls response.headers AFTER the body starts, which is too late.
from starlette.middleware.base import BaseHTTPMiddleware

# In-memory sliding-window rate limiter (keyed by IP)
_rate_store: dict = collections.defaultdict(list)
_RATE_AUTH_LIMIT   = 60   # requests / 60s on auth routes
_RATE_GLOBAL_LIMIT = 300  # requests / 60s per IP globally


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = time.time()

        # Global bucket
        gk = f"{client_ip}:g"
        _rate_store[gk] = [t for t in _rate_store[gk] if now - t < 60]
        _rate_store[gk].append(now)
        if len(_rate_store[gk]) > _RATE_GLOBAL_LIMIT:
            logger.warning("Rate limit (global) %s %s", client_ip, path)
            return JSONResponse(
                {"detail": "Rate limit exceeded. Max 300 req/min."},
                status_code=429,
                headers={"Retry-After": "60"},
            )

        # Auth-specific tighter bucket
        if "/auth/" in path:
            ak = f"{client_ip}:a"
            _rate_store[ak] = [t for t in _rate_store[ak] if now - t < 60]
            _rate_store[ak].append(now)
            if len(_rate_store[ak]) > _RATE_AUTH_LIMIT:
                logger.warning("Rate limit (auth) %s", client_ip)
                return JSONResponse(
                    {"detail": "Too many auth attempts. Try again in 60s."},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"]        = "DENY"
        response.headers["X-XSS-Protection"]       = "1; mode=block"
        response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()
        request.state.request_id = request_id

        response = await call_next(request)
        elapsed = (time.time() - start) * 1000
        response.headers["X-Request-ID"] = request_id

        path = request.url.path
        if not path.startswith("/assets") and not path.endswith(
            (".js", ".css", ".png", ".ico", ".svg", ".woff2")
        ):
            logger.info(
                "[%s] %s %s → %d (%.1fms)",
                request_id, request.method, path, response.status_code, elapsed,
            )
        return response


# ── Register Middleware (order: last added = outermost/first to run) ─────────
# Execution order: RequestLogging → SecurityHeaders → RateLimit → Route handler
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)


# ── Global Exception Handler ────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# ── API Routes ───────────────────────────────────────────────────
from backend.app.api.v1 import auth, analysis, portfolio, trading, backtest, audit

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(analysis.router, prefix=settings.API_V1_PREFIX)
app.include_router(portfolio.router, prefix=settings.API_V1_PREFIX)
app.include_router(trading.router, prefix=settings.API_V1_PREFIX)
app.include_router(backtest.router, prefix=settings.API_V1_PREFIX)
app.include_router(audit.router, prefix=settings.API_V1_PREFIX)

# ── Legacy API Routes (backward compatibility) ──────────────────
from backend.api.routes import analysis as legacy_analysis
from backend.api.routes import auth as legacy_auth
from backend.api.routes import portfolio as legacy_portfolio
from backend.api.routes import execution as legacy_execution
from backend.api.routes import backtest as legacy_backtest
from backend.api.routes import ws as legacy_ws

app.include_router(legacy_analysis.router)
app.include_router(legacy_auth.router)
app.include_router(legacy_portfolio.router)
app.include_router(legacy_execution.router)
app.include_router(legacy_backtest.router)
app.include_router(legacy_ws.router)


# ── Health & Readiness ───────────────────────────────────────────
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "demo_mode": settings.DEMO_MODE,
        "ai_provider": "openai" if settings.has_openai_key else "deterministic_fallback",
    }


@app.get("/ready", tags=["System"])
def readiness_check():
    """Checks database connectivity and critical service availability."""
    from backend.app.database import SessionLocal
    checks = {"database": False, "broker": False}

    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = True
    except Exception:
        pass

    try:
        from backend.execution.paper_broker import broker
        broker.get_summary()
        checks["broker"] = True
    except Exception:
        pass

    all_ready = all(checks.values())
    return {"status": "ready" if all_ready else "degraded", "checks": checks}


# ── Static Files (Frontend) ─────────────────────────────────────
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
react_dist = frontend_dir / "dist"

if react_dist.exists():
    # Serve React production build
    app.mount("/assets", StaticFiles(directory=str(react_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        """Serve React SPA with client-side routing support."""
        file_path = react_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(react_dist / "index.html"))
else:
    # Serve legacy vanilla frontend
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

        @app.get("/")
        async def serve_index():
            return FileResponse(str(frontend_dir / "index.html"))

        @app.get("/{filename:path}")
        async def serve_frontend_file(filename: str):
            file_path = frontend_dir / filename
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(frontend_dir / "index.html"))
