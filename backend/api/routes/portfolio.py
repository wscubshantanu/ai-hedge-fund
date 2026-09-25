from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import yfinance as yf

from src.quant.portfolio_optimizer import optimize_portfolio_markowitz, black_litterman_allocation
from src.quant.monte_carlo import run_monte_carlo_simulation
from src.quant.technical_indicators import get_market_technicals
from src.quant.regime_detector import detect_market_regime
from src.api.schemas import PortfolioOptimizationRequest
from src.db.db_manager import db
from backend.execution.paper_broker import broker

router = APIRouter(prefix="/api/v1", tags=["Portfolio Optimization & Simulation"])

@router.get("/portfolio/summary")
def get_portfolio_summary():
    try:
        return broker.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio/holdings")
def get_portfolio_holdings():
    try:
        summary = broker.get_summary()
        return {
            "cash_balance": summary["cash_balance"],
            "total_portfolio_value": summary["total_portfolio_value"],
            "total_pnl_dollars": summary["total_pnl_dollars"],
            "total_pnl_pct": summary["total_pnl_pct"],
            "holdings": summary["holdings"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel, Field

class PortfolioRebalanceRequest(BaseModel):
    target_weights: Dict[str, float] = Field(..., example={"NVDA": 0.45, "AAPL": 0.40, "MSFT": 0.15})
    current_prices: Dict[str, float] = Field(default_factory=dict)

@router.post("/portfolio/rebalance")
def rebalance_portfolio(req: PortfolioRebalanceRequest):
    try:
        prices = req.current_prices or {}
        # Fetch prices for any missing tickers
        for t in req.target_weights.keys():
            if t not in prices or prices[t] <= 0:
                try:
                    tech = get_market_technicals(t)
                    prices[t] = tech.get("current_price", 150.0)
                except Exception:
                    prices[t] = 150.0

        result = broker.execute_batch_rebalance(req.target_weights, prices)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebalance failed: {str(e)}")

@router.post("/portfolio/optimize")
def optimize_portfolio(req: PortfolioOptimizationRequest):
    try:
        tickers = [t.upper().strip() for t in req.tickers]
        mpt = optimize_portfolio_markowitz(tickers, risk_free_rate=req.risk_free_rate)
        
        agent_views = req.custom_views or {t: 0.15 for t in tickers}
        agent_conf = {t: 0.75 for t in tickers}
        bl = black_litterman_allocation(tickers, agent_views, agent_conf)
        
        return {
            "status": "success",
            "mpt": mpt,
            "black_litterman": bl
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monte-carlo/{ticker}")
def monte_carlo_asset(ticker: str, days: int = Query(default=60, ge=10, le=252), simulations: int = Query(default=2000, ge=500, le=5000)):
    ticker = ticker.upper().strip()
    try:
        tech = get_market_technicals(ticker)
        return run_monte_carlo_simulation(
            current_price=tech["current_price"],
            annual_volatility=tech["annualized_volatility"],
            forecast_days=days,
            num_simulations=simulations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regime")
def market_regime():
    try:
        df = yf.Ticker("SPY").history(period="6mo")
        return detect_market_regime(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/recent")
def recent_orders(limit: int = Query(default=10, ge=1, le=50)):
    try:
        return {"recent_orders": db.get_recent_orders(limit=limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
