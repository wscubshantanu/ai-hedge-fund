"""
AETHER Capital — Paper Trading Execution Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.core.security import get_optional_user
from backend.app.core.guardrails import apply_financial_guardrails
from backend.app.schemas import TradeOrderRequest
from backend.execution.paper_broker import broker

router = APIRouter(tags=["Paper Trading Execution"])


@router.post("/trade/preview")
def preview_trade(req: TradeOrderRequest):
    """Preview a trade order with guardrail checks (no execution)."""
    ticker = req.ticker.upper().strip()
    try:
        from src.quant.technical_indicators import get_market_technicals
        tech = get_market_technicals(ticker)
        current_price = tech["current_price"]
        vol = tech["annualized_volatility"]
    except Exception:
        current_price = 100.0
        vol = 0.25

    summary = broker.get_summary()
    portfolio_exposure = 1.0 - (summary.get("cash_pct", 100) / 100.0)

    alloc = req.allocation_pct or 0.10
    sl = req.stop_loss or current_price * 0.93
    tp = req.take_profit or current_price * 1.15

    guardrail = apply_financial_guardrails(
        ticker=ticker, action=req.side.upper(), allocation_pct=alloc,
        current_price=current_price, stop_loss=sl, take_profit=tp,
        annual_volatility=vol, portfolio_exposure=portfolio_exposure,
    )

    estimated_value = summary.get("total_value", 100000) * guardrail.allocation
    estimated_shares = estimated_value / current_price if current_price > 0 else 0

    return {
        "ticker": ticker,
        "side": guardrail.action,
        "current_price": round(current_price, 2),
        "estimated_shares": round(estimated_shares, 2),
        "estimated_cost": round(estimated_value, 2),
        "guardrails": guardrail.to_dict(),
    }


@router.post("/trade/execute")
def execute_trade(req: TradeOrderRequest, user=Depends(get_optional_user),
                  db: Session = Depends(get_db)):
    """Execute a paper trade with guardrail enforcement."""
    ticker = req.ticker.upper().strip()

    try:
        from src.quant.technical_indicators import get_market_technicals
        tech = get_market_technicals(ticker)
        current_price = tech["current_price"]
        vol = tech["annualized_volatility"]
    except Exception:
        current_price = 100.0
        vol = 0.25

    summary = broker.get_summary()
    portfolio_exposure = 1.0 - (summary.get("cash_pct", 100) / 100.0)

    alloc = req.allocation_pct or 0.10
    sl = req.stop_loss or current_price * 0.93
    tp = req.take_profit or current_price * 1.15

    guardrail = apply_financial_guardrails(
        ticker=ticker, action=req.side.upper(), allocation_pct=alloc,
        current_price=current_price, stop_loss=sl, take_profit=tp,
        annual_volatility=vol, portfolio_exposure=portfolio_exposure,
    )

    if guardrail.decision == "VETOED":
        if user:
            db.add(AuditLog(user_id=user.id, event_type="TRADE_VETOED", ticker=ticker,
                            action=guardrail.action, details=guardrail.to_dict()))
            db.commit()
        return {
            "status": "VETOED",
            "guardrails": guardrail.to_dict(),
            "portfolio": broker.get_summary(),
        }

    try:
        result = broker.execute_order(
            ticker=ticker,
            action=guardrail.action,
            target_allocation_pct=guardrail.allocation,
            current_price=current_price,
        )
        result["guardrails"] = guardrail.to_dict()

        if user:
            db.add(AuditLog(user_id=user.id, event_type="TRADE_EXECUTED", ticker=ticker,
                            action=guardrail.action, details=result))
            db.commit()

        return {"status": "FILLED", "trade": result, "portfolio": broker.get_summary()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.get("/trades")
def get_trade_history():
    """Get paper trading history."""
    try:
        summary = broker.get_summary()
        return {"trades": summary.get("recent_trades", []), "total_trades": len(summary.get("recent_trades", []))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
