import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.analysis import router as analysis_router
from src.api.routes.portfolio import router as portfolio_router
from src.api.routes.backtest import router as backtest_router
from src.api.routes.ws import router as ws_router

app = FastAPI(
    title="AETHER Capital: Institutional AI Hedge Fund API",
    description="Enterprise Multi-Agent Quantitative Research, MPT Portfolio Optimizer & Stochastic Risk Engine",
    version="3.6.0"
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
app.include_router(analysis_router)
app.include_router(portfolio_router)
app.include_router(backtest_router)
app.include_router(ws_router)

@app.get("/api/v1/health", tags=["System Diagnostics"])
def health_check():
    return {
        "status": "healthy",
        "service": "AETHER Capital Institutional API",
        "version": "3.6.0",
        "active_models": ["LangGraph", "Black-Litterman", "Monte-Carlo-GBM", "DCF-Gordon"],
        "database": "SQLite3 Persistent Audit Log",
        "caching": "L1/L2 Memory & SQLite Store"
    }

# Mount Frontend Static Web Application (HTML, CSS, JS)
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
