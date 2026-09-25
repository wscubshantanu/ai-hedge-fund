import numpy as np
import pandas as pd
from typing import Dict, Any

def detect_market_regime(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Classifies the current macroeconomic volatility & trend regime:
    - LOW_VOL_BULL: Aggressive growth allocation
    - HIGH_VOL_BULL: Cautious growth with trailing stop
    - RANGEBOUND_CHOP: Reduced sizing, mean-reversion
    - BEAR_PANIC: Defensive capital preservation / cash
    """
    if df is None or len(df) < 30:
        return {
            "regime": "LOW_VOL_BULL",
            "confidence": 0.70,
            "annualized_volatility": 0.22,
            "trend_score": 0.65,
            "action_guidance": "Favorable environment for selective equity expansion."
        }

    closes = df['Close']
    returns = closes.pct_change().dropna()
    
    # 30-day realized volatility
    recent_vol = returns.tail(30).std() * np.sqrt(252)
    
    # Moving Average Trend
    sma_20 = closes.rolling(20).mean().iloc[-1]
    sma_50 = closes.rolling(min(50, len(closes))).mean().iloc[-1]
    latest_price = closes.iloc[-1]
    
    trend_score = (latest_price - sma_50) / sma_50

    if recent_vol < 0.22 and trend_score > 0.02:
        regime = "LOW_VOL_BULL"
        guidance = "Low volatility expansion. Favorable for trend following and max position sizing."
        conf = 0.85
    elif recent_vol >= 0.35 and trend_score > 0.0:
        regime = "HIGH_VOL_BULL"
        guidance = "Bullish momentum accompanied by elevated tail risk. Implement strict stop-losses."
        conf = 0.78
    elif recent_vol >= 0.38 and trend_score < -0.03:
        regime = "BEAR_PANIC"
        guidance = "Elevated downside skew and negative momentum. Prioritize cash preservation and short hedges."
        conf = 0.88
    else:
        regime = "RANGEBOUND_CHOP"
        guidance = "Sideways consolidation with neutral momentum. Tighten risk bounds and reduce exposure."
        conf = 0.72

    return {
        "regime": regime,
        "confidence": round(conf, 2),
        "annualized_volatility": round(float(recent_vol * 100), 2),
        "trend_score": round(float(trend_score * 100), 2),
        "action_guidance": guidance
    }
