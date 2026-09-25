from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from src.graph.workflow import create_hedge_fund_graph
from src.quant.valuation_models import get_fundamental_metrics
from src.quant.technical_indicators import get_market_technicals
from src.data.news_sentiment import fetch_asset_sentiment
from src.data.cache_manager import cache
from src.db.db_manager import db

router = APIRouter(prefix="/api/v1", tags=["Analysis & Quantitative Models"])

@router.get("/analyze/{ticker}")
def analyze_asset(ticker: str):
    ticker = ticker.upper().strip()
    cache_key = f"analysis_{ticker}"
    cached_res = cache.get(cache_key)
    if cached_res:
        cached_res["_cached"] = True
        return cached_res

    try:
        workflow = create_hedge_fund_graph()
        initial_state = {
            "ticker": ticker,
            "debate_round": 0,
            "debate_history": [],
            "bull_arguments": [],
            "bear_arguments": [],
            "logs": []
        }
        final_state = workflow.invoke(initial_state)
        
        order = final_state["final_order"]
        # Persist audit record in local SQLite database
        try:
            db.save_order(order)
        except Exception:
            pass

        response_payload = {
            "ticker": ticker,
            "status": "success",
            "decision": order,
            "risk_audit": final_state["risk_assessment"],
            "technicals": final_state["technical_analysis"],
            "debate_summary": {
                "rounds_completed": final_state.get("debate_round", 0),
                "bull_arguments": final_state.get("bull_arguments", []),
                "bear_arguments": final_state.get("bear_arguments", [])
            },
            "_cached": False
        }

        # Cache for 1 hour (3600s)
        cache.set(cache_key, response_payload, ttl_seconds=3600)
        return response_payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis engine failed: {str(e)}")

@router.get("/valuation/{ticker}")
def valuation_asset(ticker: str):
    ticker = ticker.upper().strip()
    cache_key = f"valuation_{ticker}"
    cached_val = cache.get(cache_key)
    if cached_val:
        return cached_val
    try:
        val = get_fundamental_metrics(ticker)
        cache.set(cache_key, val, ttl_seconds=7200)
        return val
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/technicals/{ticker}")
def technicals_asset(ticker: str):
    ticker = ticker.upper().strip()
    try:
        return get_market_technicals(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment/{ticker}")
def sentiment_asset(ticker: str):
    ticker = ticker.upper().strip()
    try:
        return fetch_asset_sentiment(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
