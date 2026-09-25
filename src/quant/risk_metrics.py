import numpy as np
from typing import Dict, Any

def calculate_parametric_var(volatility_annual: float, confidence_level: float = 0.95, horizon_days: int = 1) -> float:
    """Calculate Parametric Value-at-Risk (VaR) as a positive percentage."""
    # Z-score for standard confidence intervals
    z_scores = {0.90: 1.282, 0.95: 1.645, 0.99: 2.326}
    z = z_scores.get(confidence_level, 1.645)
    
    daily_vol = volatility_annual / np.sqrt(252)
    var = z * daily_vol * np.sqrt(horizon_days)
    return round(float(var * 100), 2)

def evaluate_portfolio_risk(
    ticker: str,
    annual_volatility: float,
    current_price: float,
    max_vol_limit: float = 0.65,
    target_risk_budget: float = 0.12
) -> Dict[str, Any]:
    """
    Chief Risk Officer (CRO) rule engine:
    - Calculates 95% and 99% 1-day Value at Risk
    - Computes inverse-volatility sizing constraint
    - Flags risk veto if volatility breaches acceptable institutional boundaries
    """
    var_95 = calculate_parametric_var(annual_volatility, confidence_level=0.95)
    var_99 = calculate_parametric_var(annual_volatility, confidence_level=0.99)

    is_vetoed = bool(annual_volatility > max_vol_limit)
    
    # Risk-parity position sizing: allocation = target_risk_budget / volatility
    raw_allocation = target_risk_budget / (annual_volatility + 1e-6)
    capped_allocation = round(float(max(0.02, min(0.25, raw_allocation))), 3)
    
    if is_vetoed:
        capped_allocation = 0.0
        risk_rating = "EXTREME"
        summary = f"VETO: Annualized volatility ({annual_volatility*100:.1f}%) exceeds fund threshold ({max_vol_limit*100:.0f}%)."
    elif annual_volatility > 0.45:
        risk_rating = "HIGH"
        summary = f"CAUTION: Elevated volatility ({annual_volatility*100:.1f}%). Daily 95% VaR is {var_95}%. Allocation capped at {capped_allocation*100:.1f}%."
    elif annual_volatility > 0.25:
        risk_rating = "MODERATE"
        summary = f"ACCEPTABLE: Normal market regime. Daily 95% VaR is {var_95}%. Suggested max weight: {capped_allocation*100:.1f}%."
    else:
        risk_rating = "LOW"
        summary = f"FAVORABLE: Low volatility regime ({annual_volatility*100:.1f}%). Strong capital preservation metrics."

    return {
        "ticker": ticker,
        "is_vetoed": is_vetoed,
        "max_position_size_pct": capped_allocation,
        "var_95": var_95,
        "var_99": var_99,
        "risk_rating": risk_rating,
        "risk_summary": summary,
        "suggested_stop_loss": round(current_price * (1.0 - (var_95 / 100.0) * 1.5), 2),
        "suggested_take_profit": round(current_price * (1.0 + (var_95 / 100.0) * 3.0), 2)
    }
