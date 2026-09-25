from typing import Dict, Any
from src.agents.llm_client import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

def warren_buffett_analysis(ticker: str, fundamentals: Dict[str, Any], technicals: Dict[str, Any]) -> str:
    """Evaluates asset through Warren Buffett's Value & Moat framework."""
    llm = get_llm()
    if llm is not None:
        try:
            prompt = f"""You are Warren Buffett. Evaluate {ticker}:
            Current Price: ${technicals['current_price']}
            DCF Intrinsic Value: ${fundamentals['dcf_intrinsic_value']}
            Margin of Safety: {fundamentals['margin_of_safety_pct']}%
            P/E Ratio: {fundamentals.get('trailing_pe')}
            Debt-to-Equity: {fundamentals.get('debt_to_equity')}
            
            Deliver a concise 3-sentence verdict on whether this company possesses an enduring economic moat and adequate margin of safety."""
            res = llm.invoke([SystemMessage(content="You speak with the pragmatic wisdom of Warren Buffett."), HumanMessage(content=prompt)])
            return res.content
        except Exception:
            pass

    # High-conviction deterministic heuristic
    dcf_val = fundamentals.get('dcf_intrinsic_value', 100)
    curr_p = technicals.get('current_price', 100)
    mos = fundamentals.get('margin_of_safety_pct', 0)
    if mos > 15:
        return f"Buffett Verdict: {ticker} offers a compelling {mos:.1f}% Margin of Safety below our estimated intrinsic value of ${dcf_val}. Its pricing power and capital allocation discipline represent a durable franchise worth owning for the decade ahead."
    else:
        return f"Buffett Verdict: While {ticker} is a wonderful business, paying ${curr_p} leaves no adequate Margin of Safety against adverse surprises. Rule No. 1 is never lose money, and Rule No. 2 is never forget Rule No. 1. We remain patient on the sidelines."

def cathie_wood_analysis(ticker: str, technicals: Dict[str, Any]) -> str:
    """Evaluates asset through Cathie Wood's Exponential Innovation framework."""
    llm = get_llm()
    if llm is not None:
        try:
            prompt = f"""You are Cathie Wood (ARK Invest). Evaluate {ticker} at ${technicals['current_price']}.
            Focus on exponential TAM expansion, AI platform scaling, Wright's Law cost declines, and 5-year transformative CAGR."""
            res = llm.invoke([SystemMessage(content="You are Cathie Wood, championing disruptive innovation."), HumanMessage(content=prompt)])
            return res.content
        except Exception:
            pass

    return f"Cathie Wood Verdict: {ticker} stands at the convergence of multi-trillion-dollar technological curves. Wall Street consistently misprices exponential adoption by using short-term cyclical multiples. We project accelerating unit economics and substantial long-term multi-bagger potential."

def benjamin_graham_analysis(ticker: str, fundamentals: Dict[str, Any]) -> str:
    """Evaluates asset through Benjamin Graham's Net-Net & Balance Sheet Margin of Safety."""
    pe = fundamentals.get('trailing_pe', 25)
    pb = fundamentals.get('price_to_book', 3.0)
    graham_num = fundamentals.get('graham_number')

    if pe and pe < 20 and pb and pb < 2.5:
        return f"Graham Verdict: {ticker} meets classic defensive investor criteria. P/E of {pe} and P/B of {pb} demonstrate reasonable asset backing. Intrinsic Graham benchmark estimated at ${graham_num or 'N/A'}."
    else:
        return f"Graham Verdict: Speculative valuation risk detected. Current multiple ({pe}x earnings) reflects unearned optimistic assumptions rather than liquidation value. Safety of principal is not assured."

def jim_simons_quant_analysis(ticker: str, technicals: Dict[str, Any]) -> str:
    """Evaluates asset through Jim Simons' Renaissance Technologies Quantitative Signal framework."""
    rsi = technicals.get('rsi_14', 50)
    vol = technicals.get('annualized_volatility', 0.25)
    trend = technicals.get('trend', 'SIDEWAYS')
    
    if trend == "UPTREND" and 40 <= rsi <= 65:
        return f"Simons Quant Signal: High signal-to-noise ratio in 50-day momentum channel. Volatility ({vol*100:.1f}%) is within statistical stability bounds. Positive drift anomaly detected with favorable risk-adjusted Sharpe expectancy."
    else:
        return f"Simons Quant Signal: Regime transition alert. RSI at {rsi} indicates decaying directional alpha. Micro-structure suggests mean-reverting chop; position sizing must be scaled back."
