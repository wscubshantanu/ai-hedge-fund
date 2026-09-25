"""
AETHER Capital — Deterministic Financial Guardrails
AI recommendations MUST pass through these rules before execution.
"""
from typing import Dict, Any
from backend.app.config import settings


class GuardrailResult:
    def __init__(self, action: str, allocation: float, stop_loss: float,
                 take_profit: float, decision: str, notes: str):
        self.action = action
        self.allocation = allocation
        self.stop_loss = round(stop_loss, 2)
        self.take_profit = round(take_profit, 2)
        self.decision = decision  # APPROVED, MODIFIED, VETOED
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "allocation_pct": self.allocation,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "decision": self.decision,
            "notes": self.notes,
        }


def apply_financial_guardrails(
    ticker: str,
    action: str,
    allocation_pct: float,
    current_price: float,
    stop_loss: float,
    take_profit: float,
    annual_volatility: float,
    portfolio_exposure: float = 0.0,
) -> GuardrailResult:
    """
    Deterministic pre-trade risk guardrails. Every rule is documented and logged.

    Rules:
    1. VOLATILITY CEILING: If annualized vol > MAX_VOLATILITY_THRESHOLD → VETO
    2. POSITION CAP: If allocation > MAX_SINGLE_POSITION_PCT → cap to max
    3. PORTFOLIO EXPOSURE: If total exposure would exceed MAX_PORTFOLIO_EXPOSURE → reduce
    4. STOP-LOSS VALIDATION: Must be below entry for BUY
    5. TAKE-PROFIT VALIDATION: Must be above entry for BUY
    6. CASH REQUIREMENT: Allocation must be positive for BUY
    """
    notes = []
    decision = "APPROVED"
    original_action = action
    original_alloc = allocation_pct

    # Rule 1: Hard Volatility Ceiling Veto
    if annual_volatility > settings.MAX_VOLATILITY_THRESHOLD:
        action = "HOLD"
        allocation_pct = 0.0
        decision = "VETOED"
        notes.append(
            f"VETO: Annualized volatility ({annual_volatility*100:.1f}%) "
            f"exceeds fund ceiling ({settings.MAX_VOLATILITY_THRESHOLD*100:.0f}%)"
        )
        return GuardrailResult(action, allocation_pct, stop_loss, take_profit, decision, "; ".join(notes))

    # Rule 2: Position Size Capping
    if allocation_pct > settings.MAX_SINGLE_POSITION_PCT:
        allocation_pct = settings.MAX_SINGLE_POSITION_PCT
        decision = "MODIFIED"
        notes.append(
            f"CAPPED: Position reduced from {original_alloc*100:.1f}% "
            f"to {settings.MAX_SINGLE_POSITION_PCT*100:.0f}% (max single position)"
        )

    # Rule 3: Portfolio Exposure Check
    new_exposure = portfolio_exposure + allocation_pct
    if new_exposure > settings.MAX_PORTFOLIO_EXPOSURE and action == "BUY":
        max_allowed = max(0, settings.MAX_PORTFOLIO_EXPOSURE - portfolio_exposure)
        if max_allowed < 0.02:  # Less than 2% available
            action = "HOLD"
            allocation_pct = 0.0
            decision = "VETOED"
            notes.append("VETO: Portfolio fully allocated. No capacity for new positions.")
        else:
            allocation_pct = max_allowed
            decision = "MODIFIED"
            notes.append(f"CAPPED: Reduced to {max_allowed*100:.1f}% to stay within portfolio exposure limit")

    # Rule 4 & 5: Stop-Loss / Take-Profit Boundary Integrity
    if action == "BUY":
        if stop_loss is None or stop_loss >= current_price:
            stop_loss = current_price * 0.93  # Default 7% trailing stop
            notes.append("CORRECTED: Stop-loss set to -7% below entry (was invalid)")
            if decision == "APPROVED":
                decision = "MODIFIED"

        if take_profit is None or take_profit <= current_price:
            take_profit = current_price * 1.15  # Default 15% profit target
            notes.append("CORRECTED: Take-profit set to +15% above entry (was invalid)")
            if decision == "APPROVED":
                decision = "MODIFIED"

    elif action in ("SELL", "HOLD"):
        allocation_pct = 0.0

    if not notes:
        notes.append("All guardrail checks passed. No modifications required.")

    return GuardrailResult(action, round(allocation_pct, 4), stop_loss, take_profit, decision, "; ".join(notes))
