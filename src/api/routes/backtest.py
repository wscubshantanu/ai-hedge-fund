from fastapi import APIRouter, HTTPException, Query
from src.backtester.event_engine import run_backtest
from src.api.schemas import BacktestRequest
from src.db.db_manager import db

router = APIRouter(prefix="/api/v1", tags=["Backtesting & Historical Simulation"])

@router.post("/backtest")
def execute_backtest(req: BacktestRequest):
    try:
        res = run_backtest(
            ticker=req.ticker.upper().strip(),
            period=req.period,
            initial_capital=req.initial_capital,
            rebalance_frequency_days=req.rebalance_days,
            slippage_bps=req.slippage_bps
        )
        # Persist backtest run
        try:
            db.save_backtest(res)
        except Exception:
            pass

        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backtest/recent")
def recent_backtests(limit: int = Query(default=10, ge=1, le=50)):
    try:
        return {"recent_backtests": db.get_recent_backtests(limit=limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
