import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.portfolio import router as portfolio_router
from backend.api.routes.backtest import router as backtest_router
from backend.api.routes.execution import router as execution_router
from backend.api.routes.ws import router as ws_router
from backend.api.routes.auth import router as auth_router
from backend.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise Multi-Agent Quantitative Research, MPT Portfolio Optimizer, Stochastic Risk Engine & Live Paper Broker",
    version=settings.VERSION
)

# Enable CORS for institutional integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Modular API Routers
app.include_router(auth_router)
app.include_router(analysis_router)
app.include_router(portfolio_router)
app.include_router(backtest_router)
app.include_router(execution_router)
app.include_router(ws_router)

@app.get("/api/v1/health", tags=["System Diagnostics"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "active_engines": [
            "LangGraph Dialectic StateGraph",
            "Modern Portfolio Theory (Markowitz & Black-Litterman)",
            "2,000-Path Monte Carlo GBM",
            "5-Year DCF Gordon Growth",
            "Paper Trading Brokerage Engine"
        ],
        "database": "SQLite3 Persistent Audit Log",
        "cache": "L1/L2 Memory & SQLite Store"
    }

# Mount Frontend Static Web Application (HTML, CSS, JS)
frontend_dir = root_dir / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
