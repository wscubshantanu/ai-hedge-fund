from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.execution.paper_broker import broker
from backend.core.guardrails import apply_financial_guardrails

router = APIRouter(prefix="/api/v1/trade", tags=["Live Paper Trading Execution"])

class ExecuteTradeRequest(BaseModel):
    ticker: str = Field(default="NVDA", example="NVDA")
    action: str = Field(default="BUY", example="BUY")
    target_allocation_pct: float = Field(default=0.25, ge=0.0, le=1.0)
    current_price: float = Field(default=150.0)
    stop_loss_price: float = Field(default=143.0)
    take_profit_price: float = Field(default=165.0)
    annual_volatility: float = Field(default=0.28)

@router.post("/preflight")
def preflight_order_check(req: ExecuteTradeRequest):
    try:
        action, alloc, sl, tp, guardrail_note = apply_financial_guardrails(
            ticker=req.ticker,
            action=req.action,
            allocation_pct=req.target_allocation_pct,
            current_price=req.current_price,
            stop_loss=req.stop_loss_price,
            take_profit=req.take_profit_price,
            annual_volatility=req.annual_volatility
        )
        status = "APPROVED"
        if "VETO" in guardrail_note.upper():
            status = "VETOED"
        elif "CAPPED" in guardrail_note.upper() or alloc < req.target_allocation_pct:
            status = "CAPPED"

        return {
            "status": status,
            "original_action": req.action,
            "approved_action": action,
            "original_allocation_pct": req.target_allocation_pct,
            "approved_allocation_pct": alloc,
            "stop_loss": sl,
            "take_profit": tp,
            "notes": guardrail_note
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
def execute_order(req: ExecuteTradeRequest):
    try:
        # 1. Apply Deterministic Financial Guardrails
        action, alloc, sl, tp, guardrail_note = apply_financial_guardrails(
            ticker=req.ticker,
            action=req.action,
            allocation_pct=req.target_allocation_pct,
            current_price=req.current_price,
            stop_loss=req.stop_loss_price,
            take_profit=req.take_profit_price,
            annual_volatility=req.annual_volatility
        )

        # 2. Transmit to Paper Broker
        result = broker.execute_order(
            ticker=req.ticker,
            action=action,
            target_allocation_pct=alloc,
            current_price=req.current_price
        )
        result["guardrails"] = guardrail_note
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order execution rejected: {str(e)}")

@router.get("/portfolio")
def get_portfolio_summary():
    try:
        return broker.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portfolio/reset")
def reset_portfolio_balance():
    try:
        return broker.reset_portfolio()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
