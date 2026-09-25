"""
AETHER Capital — Portfolio, Optimization, Monte Carlo, & Risk Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import yfinance as yf

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.core.security import get_optional_user
from backend.app.schemas import PortfolioOptimizeRequest, MonteCarloRequest

# Existing quant modules
from src.quant.portfolio_optimizer import optimize_portfolio_markowitz, black_litterman_allocation
from src.quant.monte_carlo import run_monte_carlo_simulation
from src.quant.technical_indicators import get_market_technicals
from src.quant.risk_metrics import evaluate_portfolio_risk, calculate_parametric_var
from src.quant.regime_detector import detect_market_regime
from backend.execution.paper_broker import broker
from src.db.db_manager import db as legacy_db

router = APIRouter(tags=["Portfolio, Risk & Simulation"])


@router.post("/portfolio/optimize")
def optimize_portfolio(req: PortfolioOptimizeRequest):
    """Run Markowitz MPT + Black-Litterman optimization."""
    try:
        tickers = [t.upper().strip() for t in req.tickers]
        mpt = optimize_portfolio_markowitz(tickers, risk_free_rate=req.risk_free_rate)

        agent_views = req.custom_views or {t: 0.15 for t in tickers}
        agent_conf = {t: 0.75 for t in tickers}
        bl = black_litterman_allocation(tickers, agent_views, agent_conf)

        return {"status": "success", "mpt": mpt, "black_litterman": bl}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio")
def get_portfolio():
    """Get current paper trading portfolio state."""
    try:
        return broker.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/reset")
def reset_portfolio():
    """Reset paper trading portfolio to initial $100,000."""
    try:
        return broker.reset_portfolio()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/risk")
def portfolio_risk():
    """Get risk dashboard for current portfolio."""
    try:
        summary = broker.get_summary()
        positions = summary.get("positions", {})

        risk_data = {
            "total_value": summary.get("total_value", 100000),
            "cash_pct": summary.get("cash_pct", 100),
            "positions_count": len(positions),
            "concentration": {},
        }

        # Per-position risk
        for ticker, pos in positions.items():
            try:
                tech = get_market_technicals(ticker, period="3mo")
                vol = tech.get("annualized_volatility", 0.25)
                var_95 = calculate_parametric_var(vol, confidence_level=0.95)
                risk_data["concentration"][ticker] = {
                    "weight_pct": pos.get("weight_pct", 0),
                    "volatility": round(vol * 100, 2),
                    "var_95_pct": round(var_95, 2),
                }
            except Exception:
                risk_data["concentration"][ticker] = {"weight_pct": pos.get("weight_pct", 0)}

        # Market regime
        try:
            spy_df = yf.Ticker("SPY").history(period="6mo")
            risk_data["market_regime"] = detect_market_regime(spy_df)
        except Exception:
            risk_data["market_regime"] = {"regime": "UNKNOWN"}

        return risk_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monte-carlo/{ticker}")
def run_monte_carlo(ticker: str, days: int = Query(60, ge=10, le=252),
                    simulations: int = Query(2000, ge=500, le=5000)):
    """Run Monte Carlo GBM simulation."""
    ticker = ticker.upper().strip()
    try:
        tech = get_market_technicals(ticker)
        result = run_monte_carlo_simulation(
            current_price=tech["current_price"],
            annual_volatility=tech["annualized_volatility"],
            forecast_days=days,
            num_simulations=simulations,
        )
        result["ticker"] = ticker
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Also support GET for backwards compatibility
@router.get("/monte-carlo/{ticker}")
def run_monte_carlo_get(ticker: str, days: int = Query(60, ge=10, le=252),
                        simulations: int = Query(2000, ge=500, le=5000)):
    return run_monte_carlo(ticker, days, simulations)


@router.get("/regime")
def market_regime():
    """Detect current macroeconomic regime."""
    try:
        df = yf.Ticker("SPY").history(period="6mo")
        return detect_market_regime(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/recent")
def recent_orders(limit: int = Query(10, ge=1, le=50)):
    """Get recent trade orders from audit log."""
    try:
        return {"recent_orders": legacy_db.get_recent_orders(limit=limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
