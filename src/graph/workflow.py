import os
from langgraph.graph import StateGraph, END
from src.agents.state import AgentState, AnalystSignal, FinalTradeOrder, RiskEvaluation
from src.quant.technical_indicators import get_market_technicals
from src.quant.risk_metrics import evaluate_portfolio_risk
from src.agents.llm_client import invoke_structured_or_fallback, get_llm

def technical_node(state: AgentState) -> dict:
    ticker = state["ticker"]
    tech = get_market_technicals(ticker)
    
    prompt = f"""Analyze technical indicators for {ticker}:
    Price: ${tech['current_price']} (Change: {tech['change_pct']}%)
    Trend: {tech['trend']} | SMA 20: ${tech['sma_20']} | SMA 50: ${tech['sma_50']} | SMA 200: ${tech['sma_200']}
    RSI (14): {tech['rsi_14']} (Overbought > 70, Oversold < 30)
    MACD: {tech['macd']} vs Signal: {tech['macd_signal']}
    Annualized Volatility: {tech['annualized_volatility'] * 100:.1f}%
    
    Determine signal (BULLISH/BEARISH/NEUTRAL), conviction confidence (0-1), and 3 bullet points."""
    
    signal_type = "BULLISH" if tech['trend'] == "UPTREND" and not tech['is_overbought'] else (
        "BEARISH" if tech['trend'] == "DOWNTREND" or tech['is_overbought'] else "NEUTRAL"
    )
    conf = 0.80 if tech['trend'] == "UPTREND" else 0.60

    fallback = {
        "agent_name": "TechnicalAnalyst",
        "signal": signal_type,
        "confidence": conf,
        "key_points": [
            f"Asset currently in {tech['trend']} with Price at ${tech['current_price']}.",
            f"RSI-14 is at {tech['rsi_14']}, indicating {'overbought' if tech['is_overbought'] else 'healthy momentum'}.",
            f"MACD histogram at {tech['macd_hist']} confirms {signal_type.lower()} directional momentum."
        ],
        "metrics_summary": f"SMA50: ${tech['sma_50']}, Volatility: {tech['annualized_volatility']*100:.1f}%"
    }
    
    report = invoke_structured_or_fallback(
        prompt=prompt,
        system_prompt="You are a Senior Quantitative Technical Analyst evaluating price action.",
        schema=AnalystSignal,
        fallback_data=fallback
    )
    
    return {
        "technical_analysis": tech,
        "debate_history": state.get("debate_history", []) + [{"sender": "TechnicalAnalyst", "message": str(report.dict())}],
        "logs": state.get("logs", []) + [f"Technical analysis completed: {report.signal} ({report.confidence*100:.0f}% confidence)"]
    }

def bull_node(state: AgentState) -> dict:
    ticker = state["ticker"]
    tech = state["technical_analysis"]
    bear_args = state.get("bear_arguments", [])
    latest_bear = bear_args[-1] if bear_args else "No prior skeptic counter-argument."
    
    llm = get_llm()
    if llm is not None:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            prompt = f"Bull Thesis for {ticker} at ${tech['current_price']}. Counter this bear critique: '{latest_bear}'."
            res = llm.invoke([SystemMessage(content="You are the Lead Long Growth Strategist."), HumanMessage(content=prompt)])
            bull_text = res.content
        except Exception:
            bull_text = f"Strong institutional demand at ${tech['current_price']}. Technical support holds above ${tech['sma_50']}. Growth catalysts outweigh temporary headwind."
    else:
        bull_text = (
            f"Conviction Long on {ticker}: Current momentum supports expansion towards ${tech['52w_high']}. "
            f"Support at ${tech['sma_50']} remains robust with favorable risk/reward upside."
        )
        
    bull_list = state.get("bull_arguments", []) + [bull_text]
    return {
        "bull_arguments": bull_list,
        "debate_history": state.get("debate_history", []) + [{"sender": "BullAgent", "message": bull_text}],
        "logs": state.get("logs", []) + [f"Bull Agent posted thesis (Round {state.get('debate_round', 0) + 1})"]
    }

def bear_node(state: AgentState) -> dict:
    ticker = state["ticker"]
    tech = state["technical_analysis"]
    bull_args = state.get("bull_arguments", [])
    latest_bull = bull_args[-1] if bull_args else "No prior growth argument."
    
    llm = get_llm()
    if llm is not None:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            prompt = f"Bear Skeptic critique for {ticker} at ${tech['current_price']}. Challenge this bull thesis: '{latest_bull}'."
            res = llm.invoke([SystemMessage(content="You are a Chief Short-Seller and Forensic Risk Analyst."), HumanMessage(content=prompt)])
            bear_text = res.content
        except Exception:
            bear_text = f"Valuation caution on {ticker}. Annualized volatility of {tech['annualized_volatility']*100:.1f}% presents downside skew if macro liquidity contracts."
    else:
        bear_text = (
            f"Downside Risk on {ticker}: Elevated volatility ({tech['annualized_volatility']*100:.1f}%) and resistance near ${tech['bb_upper']} "
            f"pose severe asymmetric downside risk if multiple compression accelerates."
        )
        
    bear_list = state.get("bear_arguments", []) + [bear_text]
    current_round = state.get("debate_round", 0) + 1
    return {
        "bear_arguments": bear_list,
        "debate_round": current_round,
        "debate_history": state.get("debate_history", []) + [{"sender": "BearAgent", "message": bear_text}],
        "logs": state.get("logs", []) + [f"Bear Agent rebutted thesis (Completed Round {current_round})"]
    }

def risk_node(state: AgentState) -> dict:
    ticker = state["ticker"]
    tech = state["technical_analysis"]
    risk = evaluate_portfolio_risk(
        ticker=ticker,
        annual_volatility=tech["annualized_volatility"],
        current_price=tech["current_price"]
    )
    
    return {
        "risk_assessment": risk,
        "logs": state.get("logs", []) + [f"Risk Officer evaluated: Veto={risk['is_vetoed']}, VaR-95={risk['var_95']}%, Max Alloc={risk['max_position_size_pct']*100:.1f}%"]
    }

def portfolio_manager_node(state: AgentState) -> dict:
    ticker = state["ticker"]
    tech = state["technical_analysis"]
    risk = state["risk_assessment"]
    bull = state["bull_arguments"][-1]
    bear = state["bear_arguments"][-1]
    
    # Deterministic default logic based on risk and technicals
    if risk["is_vetoed"]:
        action = "HOLD"
        alloc = 0.0
        conf = 0.90
        thesis = f"MANDATORY RISK VETO: Position allocation suspended due to high volatility ({tech['annualized_volatility']*100:.1f}%)."
    elif tech["trend"] == "UPTREND" and not tech["is_overbought"]:
        action = "BUY"
        alloc = risk["max_position_size_pct"]
        conf = 0.82
        thesis = f"Constructive bullish alignment. Technical trend is {tech['trend']} with Price above SMA-50. Risk bounds respected."
    elif tech["trend"] == "DOWNTREND":
        action = "SELL"
        alloc = 0.0
        conf = 0.78
        thesis = f"Defensive posture. Trend breakdown under SMA-50. Capital preservation prioritized."
    else:
        action = "HOLD"
        alloc = round(risk["max_position_size_pct"] * 0.5, 3)
        conf = 0.65
        thesis = f"Neutral consolidation pattern. Recommending measured exposure until directional breakout."

    prompt = f"""You are the Chief Investment Officer (CIO).
    Ticker: {ticker} | Price: ${tech['current_price']}
    Bull Thesis: {bull}
    Bear Critique: {bear}
    Risk Officer Mandate: {risk['risk_summary']} (Veto: {risk['is_vetoed']})
    
    Formulate final trade order. If Vetoed, action must be HOLD or SELL with 0.0 allocation."""

    fallback = {
        "ticker": ticker,
        "action": action,
        "target_allocation_pct": alloc,
        "confidence": conf,
        "stop_loss_price": risk["suggested_stop_loss"],
        "take_profit_price": risk["suggested_take_profit"],
        "executive_thesis": thesis,
        "bull_bear_consensus": f"Debate concluded after {state.get('debate_round', 1)} rounds. Risk gatekeeper applied."
    }

    order = invoke_structured_or_fallback(
        prompt=prompt,
        system_prompt="You make objective capital allocation decisions for a top tier quantitative hedge fund.",
        schema=FinalTradeOrder,
        fallback_data=fallback
    )

    return {
        "final_order": order.dict(),
        "logs": state.get("logs", []) + [f"CIO Order finalized: {order.action} {ticker} ({order.target_allocation_pct*100:.1f}% allocation, {order.confidence*100:.0f}% conviction)"]
    }

def debate_decision(state: AgentState) -> str:
    """Controls multi-agent debate convergence. Caps at 2 rounds to prevent infinite loops and token bloat."""
    if state.get("debate_round", 0) >= 2:
        return "risk_node"
    return "bull_node"

def create_hedge_fund_graph():
    """Builds and compiles the complete LangGraph StateGraph workflow."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("technical_node", technical_node)
    workflow.add_node("bull_node", bull_node)
    workflow.add_node("bear_node", bear_node)
    workflow.add_node("risk_node", risk_node)
    workflow.add_node("portfolio_manager_node", portfolio_manager_node)
    
    workflow.set_entry_point("technical_node")
    workflow.add_edge("technical_node", "bull_node")
    workflow.add_edge("bull_node", "bear_node")
    
    workflow.add_conditional_edges(
        "bear_node",
        debate_decision,
        {
            "bull_node": "bull_node",
            "risk_node": "risk_node"
        }
    )
    
    workflow.add_edge("risk_node", "portfolio_manager_node")
    workflow.add_edge("portfolio_manager_node", END)
    
    return workflow.compile()
