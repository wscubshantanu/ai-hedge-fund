"""
AETHER Capital — Analysis Endpoints
Full analysis pipeline, technical, fundamental, valuation, sentiment
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.core.security import get_optional_user
from backend.app.models.audit import AuditLog
from src.data.cache_manager import cache

# Existing quant modules (preserved)
from src.quant.technical_indicators import get_market_technicals
from src.quant.valuation_models import get_fundamental_metrics
from src.data.news_sentiment import fetch_asset_sentiment
from src.graph.workflow import create_hedge_fund_graph
from src.db.db_manager import db as legacy_db

router = APIRouter(tags=["Analysis & Quantitative Models"])


def _compute_technical_score(tech: dict) -> dict:
    """Compute a 0-100 technical score from indicators."""
    score = 50.0  # Neutral baseline
    breakdown = []

    # RSI contribution (25% weight)
    rsi = tech.get("rsi_14", 50)
    if rsi < 30:
        rsi_score = 80  # Oversold = bullish
    elif rsi > 70:
        rsi_score = 20  # Overbought = bearish
    else:
        rsi_score = 50 + (50 - rsi)  # Moderate
    breakdown.append({"name": "RSI (14)", "value": rsi, "weight": 0.25,
                       "contribution": round(rsi_score * 0.25, 1),
                       "description": f"RSI={rsi:.1f}. {'Oversold (bullish)' if rsi<30 else 'Overbought (bearish)' if rsi>70 else 'Neutral zone'}"})

    # Trend contribution (30% weight)
    trend = tech.get("trend", "NEUTRAL")
    trend_map = {"BULLISH": 85, "NEUTRAL": 50, "BEARISH": 15}
    trend_score = trend_map.get(trend, 50)
    breakdown.append({"name": "Trend (SMA20/50)", "value": trend_score, "weight": 0.30,
                       "contribution": round(trend_score * 0.30, 1),
                       "description": f"Trend={trend}"})

    # MACD contribution (20% weight)
    macd_val = tech.get("macd", 0)
    macd_sig = tech.get("macd_signal", 0)
    macd_cross = "BULLISH" if macd_val > macd_sig else "BEARISH"
    macd_score = 75 if macd_cross == "BULLISH" else 25
    breakdown.append({"name": "MACD Crossover", "value": macd_score, "weight": 0.20,
                       "contribution": round(macd_score * 0.20, 1),
                       "description": f"MACD {'above' if macd_cross=='BULLISH' else 'below'} signal line"})

    # Volatility contribution (15% weight)
    vol = tech.get("annualized_volatility", 0.25)
    if vol < 0.20:
        vol_score = 80
    elif vol > 0.50:
        vol_score = 20
    else:
        vol_score = 80 - ((vol - 0.20) / 0.30) * 60
    breakdown.append({"name": "Volatility", "value": round(vol*100, 1), "weight": 0.15,
                       "contribution": round(vol_score * 0.15, 1),
                       "description": f"Annualized vol={vol*100:.1f}%"})

    # Bollinger Band position (10% weight)
    bb_pos = tech.get("bollinger_position", 0.5)
    bb_score = max(10, min(90, (1 - bb_pos) * 100))  # Lower = closer to lower band = bullish
    breakdown.append({"name": "Bollinger Position", "value": round(bb_pos, 2), "weight": 0.10,
                       "contribution": round(bb_score * 0.10, 1),
                       "description": f"Position={bb_pos:.2f} (0=lower band, 1=upper band)"})

    total_score = sum(b["contribution"] for b in breakdown)
    return {"score": round(total_score, 1), "breakdown": breakdown}


def _compute_fundamental_score(metrics: dict) -> dict:
    """Compute 0-100 fundamental score from key metrics."""
    breakdown = []
    pe = metrics.get("pe_ratio_ttm")
    pb = metrics.get("price_to_book")
    roe = metrics.get("return_on_equity")
    margins = metrics.get("profit_margins")
    rev_growth = metrics.get("revenue_growth")
    debt_eq = metrics.get("debt_to_equity")

    # P/E ratio (20%)
    if pe and pe > 0:
        pe_score = max(10, min(90, 100 - (pe / 0.5)))
    else:
        pe_score = 50
    breakdown.append({"name": "P/E Ratio", "value": pe or 0, "weight": 0.20,
                       "contribution": round(pe_score * 0.20, 1),
                       "description": f"P/E={pe:.1f}" if pe else "N/A"})

    # ROE (25%)
    if roe:
        roe_score = max(10, min(90, roe * 400))  # 22.5% ROE = 90
    else:
        roe_score = 50
    breakdown.append({"name": "Return on Equity", "value": round((roe or 0)*100, 1), "weight": 0.25,
                       "contribution": round(roe_score * 0.25, 1),
                       "description": f"ROE={roe*100:.1f}%" if roe else "N/A"})

    # Revenue Growth (20%)
    if rev_growth:
        rg_score = max(10, min(90, 50 + rev_growth * 200))
    else:
        rg_score = 50
    breakdown.append({"name": "Revenue Growth", "value": round((rev_growth or 0)*100, 1), "weight": 0.20,
                       "contribution": round(rg_score * 0.20, 1),
                       "description": f"Growth={rev_growth*100:.1f}%" if rev_growth else "N/A"})

    # Profit Margins (20%)
    if margins:
        pm_score = max(10, min(90, margins * 300))
    else:
        pm_score = 50
    breakdown.append({"name": "Profit Margins", "value": round((margins or 0)*100, 1), "weight": 0.20,
                       "contribution": round(pm_score * 0.20, 1),
                       "description": f"Margins={margins*100:.1f}%" if margins else "N/A"})

    # Debt/Equity (15%)
    if debt_eq is not None and debt_eq >= 0:
        de_score = max(10, min(90, 90 - debt_eq * 30))
    else:
        de_score = 50
    breakdown.append({"name": "Debt/Equity", "value": round(debt_eq or 0, 2), "weight": 0.15,
                       "contribution": round(de_score * 0.15, 1),
                       "description": f"D/E={debt_eq:.2f}" if debt_eq is not None else "N/A"})

    total_score = sum(b["contribution"] for b in breakdown)
    strengths = []
    weaknesses = []
    if roe and roe > 0.15:
        strengths.append(f"Strong ROE of {roe*100:.1f}% indicates efficient capital deployment")
    if margins and margins > 0.20:
        strengths.append(f"Healthy profit margins of {margins*100:.1f}%")
    if rev_growth and rev_growth > 0.10:
        strengths.append(f"Revenue growing at {rev_growth*100:.1f}% year-over-year")
    if pe and pe < 20:
        strengths.append(f"Reasonable P/E of {pe:.1f}")
    if debt_eq is not None and debt_eq < 0.5:
        strengths.append("Conservative leverage with low debt-to-equity")

    if pe and pe > 40:
        weaknesses.append(f"Elevated P/E of {pe:.1f} suggests premium valuation")
    if roe and roe < 0.08:
        weaknesses.append(f"Below-average ROE of {roe*100:.1f}%")
    if debt_eq and debt_eq > 1.5:
        weaknesses.append(f"High leverage with D/E ratio of {debt_eq:.2f}")
    if margins and margins < 0.05:
        weaknesses.append("Thin profit margins under 5%")

    return {"score": round(total_score, 1), "breakdown": breakdown,
            "strengths": strengths or ["Limited data for strength analysis"],
            "weaknesses": weaknesses or ["No significant weaknesses identified"]}


def _compute_sentiment_score(sent: dict) -> dict:
    """Convert sentiment data to 0-100 score."""
    agg = sent.get("aggregate_sentiment_score", 0)
    # Map -1..+1 range to 0..100
    score = max(0, min(100, (agg + 1) * 50))
    tone = sent.get("overall_tone", "NEUTRAL")
    headlines = sent.get("top_headlines", [])

    pos_count = sum(1 for h in headlines if h.get("sentiment_score", 0) > 0.1)
    neg_count = sum(1 for h in headlines if h.get("sentiment_score", 0) < -0.1)
    neutral_count = len(headlines) - pos_count - neg_count
    total = max(1, len(headlines))

    return {
        "score": round(score, 1),
        "positive_pct": round(pos_count / total * 100, 1),
        "neutral_pct": round(neutral_count / total * 100, 1),
        "negative_pct": round(neg_count / total * 100, 1),
        "overall_tone": tone,
        "headlines": headlines,
    }


@router.post("/analyze/{ticker}")
def full_analysis(ticker: str, user: Optional[User] = Depends(get_optional_user),
                  db: Session = Depends(get_db)):
    """Run the full multi-agent investment analysis pipeline."""
    ticker = ticker.upper().strip()
    cache_key = f"full_analysis_{ticker}"
    cached = cache.get(cache_key)
    if cached:
        cached["_cached"] = True
        return cached

    try:
        workflow = create_hedge_fund_graph()
        initial_state = {
            "ticker": ticker, "debate_round": 0,
            "debate_history": [], "bull_arguments": [],
            "bear_arguments": [], "logs": [],
        }
        final_state = workflow.invoke(initial_state)
        order = final_state["final_order"]

        # Save audit
        try:
            legacy_db.save_order(order)
        except Exception:
            pass

        # Compute scores
        tech = final_state.get("technical_analysis", {})
        tech_scored = _compute_technical_score(tech)

        try:
            fund_metrics = get_fundamental_metrics(ticker)
        except Exception:
            fund_metrics = {}
        fund_scored = _compute_fundamental_score(fund_metrics)

        try:
            sentiment_raw = fetch_asset_sentiment(ticker)
        except Exception:
            sentiment_raw = {}
        sent_scored = _compute_sentiment_score(sentiment_raw)

        # Valuation score from order context
        val_score = 55.0  # Default neutral
        if order.get("action") == "BUY":
            val_score = 65 + order.get("confidence", 0.5) * 20
        elif order.get("action") == "SELL":
            val_score = 35 - order.get("confidence", 0.5) * 15

        response = {
            "ticker": ticker,
            "status": "success",
            "scores": {
                "technical": tech_scored["score"],
                "fundamental": fund_scored["score"],
                "sentiment": sent_scored["score"],
                "valuation": round(val_score, 1),
                "overall": round((tech_scored["score"] * 0.25 + fund_scored["score"] * 0.30 +
                                   sent_scored["score"] * 0.15 + val_score * 0.30), 1),
            },
            "decision": order,
            "risk_audit": final_state.get("risk_assessment", {}),
            "technicals": {**tech, "score": tech_scored["score"], "score_breakdown": tech_scored["breakdown"]},
            "fundamentals": {**fund_metrics, "score": fund_scored["score"],
                              "strengths": fund_scored["strengths"], "weaknesses": fund_scored["weaknesses"],
                              "score_breakdown": fund_scored["breakdown"]},
            "sentiment": {**sentiment_raw, "score": sent_scored["score"]},
            "debate_summary": {
                "rounds_completed": final_state.get("debate_round", 0),
                "bull_arguments": final_state.get("bull_arguments", []),
                "bear_arguments": final_state.get("bear_arguments", []),
            },
            "_cached": False,
        }

        cache.set(cache_key, response, ttl_seconds=3600)

        # DB audit log
        if user:
            db.add(AuditLog(user_id=user.id, event_type="ANALYSIS", ticker=ticker,
                            action=order.get("action"), details={"scores": response["scores"]}))
            db.commit()

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis engine error: {str(e)}")


@router.get("/technical/{ticker}")
def get_technical(ticker: str):
    """Get technical analysis with scored breakdown."""
    ticker = ticker.upper().strip()
    cache_key = f"technical_{ticker}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        tech = get_market_technicals(ticker)
        scored = _compute_technical_score(tech)
        result = {**tech, "score": scored["score"], "score_breakdown": scored["breakdown"],
                  "data_source": "live"}
        cache.set(cache_key, result, ttl_seconds=1800)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fundamental/{ticker}")
def get_fundamental(ticker: str):
    """Get fundamental analysis with scored breakdown."""
    ticker = ticker.upper().strip()
    cache_key = f"fundamental_{ticker}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        metrics = get_fundamental_metrics(ticker)
        scored = _compute_fundamental_score(metrics)
        result = {**metrics, **scored, "data_source": "live"}
        cache.set(cache_key, result, ttl_seconds=7200)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/valuation/{ticker}")
def get_valuation(ticker: str):
    """Get DCF, Graham Number, and relative valuation."""
    ticker = ticker.upper().strip()
    cache_key = f"valuation_{ticker}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        val = get_fundamental_metrics(ticker)
        cache.set(cache_key, val, ttl_seconds=7200)
        return val
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/{ticker}")
def get_sentiment(ticker: str):
    """Get news sentiment analysis with scored breakdown."""
    ticker = ticker.upper().strip()
    try:
        raw = fetch_asset_sentiment(ticker)
        scored = _compute_sentiment_score(raw)
        return {**raw, **scored, "data_source": "yahoo_finance"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
