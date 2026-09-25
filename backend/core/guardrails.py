from typing import Dict, Any, Tuple
from backend.core.config import settings

class FinancialGuardrailError(Exception):
    pass

def apply_financial_guardrails(
    ticker: str,
    action: str,
    allocation_pct: float,
    current_price: float,
    stop_loss: float,
    take_profit: float,
    annual_volatility: float
) -> Tuple[str, float, float, float, str]:
    """
    Deterministic Financial Guardrails to prevent LLM hallucinations:
    - Enforces hard stop-loss and take-profit directional boundaries
    - Bounds position allocation to institutional risk limits
    - Automatically overrides order if asset volatility breaches fund ceiling
    """
    guardrail_note = "Guardrails verified: No violations."
    
    # 1. Hard Volatility Ceiling Veto
    if annual_volatility > settings.MAX_VOLATILITY_THRESHOLD:
        action = "HOLD"
        allocation_pct = 0.0
        guardrail_note = f"GUARDRAIL VETO: Annualized volatility ({annual_volatility*100:.1f}%) exceeds safety ceiling ({settings.MAX_VOLATILITY_THRESHOLD*100:.0f}%)."
        return action, allocation_pct, round(stop_loss, 2), round(take_profit, 2), guardrail_note

    # 2. Position Size Capping
    if allocation_pct > settings.MAX_SINGLE_POSITION_WEIGHT:
        allocation_pct = settings.MAX_SINGLE_POSITION_WEIGHT
        guardrail_note = f"GUARDRAIL CAPPED: Position allocation restricted to maximum {settings.MAX_SINGLE_POSITION_WEIGHT*100:.0f}%."

    # 3. Stop-Loss & Take-Profit Boundary Integrity
    if action == "BUY":
        if stop_loss is None or stop_loss >= current_price:
            stop_loss = current_price * 0.93  # 7% trailing stop default
            guardrail_note += " Corrected invalid stop-loss to 7% below entry."
        if take_profit is None or take_profit <= current_price:
            take_profit = current_price * 1.15 # 15% profit target default
            guardrail_note += " Corrected invalid take-profit to 15% above entry."
    elif action in ["SELL", "HOLD"]:
        allocation_pct = 0.0

    return action, round(allocation_pct, 4), round(stop_loss, 2), round(take_profit, 2), guardrail_note
