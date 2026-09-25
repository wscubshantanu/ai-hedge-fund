"""
AETHER Capital — Backtesting Endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas import BacktestRequest
from src.backtester.event_engine import run_backtest
from src.db.db_manager import db as legacy_db

router = APIRouter(tags=["Backtesting & Historical Simulation"])


@router.post("/backtest")
def execute_backtest(req: BacktestRequest):
    """Run event-driven backtest with zero lookahead bias."""
    try:
        res = run_backtest(
            ticker=req.ticker.upper().strip(),
            period=req.period,
            initial_capital=req.initial_capital,
            rebalance_frequency_days=req.rebalance_days,
            slippage_bps=req.slippage_bps,
        )

        # Add enhanced metrics
        portfolio_hist = res.get("portfolio_history", [])
        if len(portfolio_hist) > 1:
            # Win/loss tracking from portfolio changes
            daily_changes = [portfolio_hist[i] - portfolio_hist[i-1] for i in range(1, len(portfolio_hist))]
            wins = [c for c in daily_changes if c > 0]
            losses = [c for c in daily_changes if c < 0]
            res["win_rate_pct"] = round(len(wins) / max(1, len(daily_changes)) * 100, 1)
            res["profit_factor"] = round(sum(wins) / max(0.01, abs(sum(losses))), 2) if losses else 99.99
            res["avg_trade_pnl"] = round(sum(daily_changes) / max(1, len(daily_changes)), 2)

            # CAGR
            n_years = len(portfolio_hist) / 252
            if n_years > 0 and portfolio_hist[-1] > 0 and res["initial_capital"] > 0:
                res["cagr_pct"] = round(((portfolio_hist[-1] / res["initial_capital"]) ** (1/n_years) - 1) * 100, 2)
            else:
                res["cagr_pct"] = 0.0

            # Equity curve & benchmark curve
            res["equity_curve"] = portfolio_hist
            benchmark_start = res.get("initial_capital", 100000)
            if "benchmark_return_pct" in res:
                n = len(portfolio_hist)
                daily_bench = (1 + res["benchmark_return_pct"]/100) ** (1/max(1,n-1))
                res["benchmark_curve"] = [round(benchmark_start * (daily_bench ** i), 2) for i in range(n)]
        else:
            res.update({"win_rate_pct": 0, "profit_factor": 0, "avg_trade_pnl": 0, "cagr_pct": 0,
                        "equity_curve": portfolio_hist, "benchmark_curve": portfolio_hist})

        try:
            legacy_db.save_backtest(res)
        except Exception:
            pass

        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtest/recent")
def recent_backtests(limit: int = Query(10, ge=1, le=50)):
    """Get recent backtest runs."""
    try:
        return {"recent_backtests": legacy_db.get_recent_backtests(limit=limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
