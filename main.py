import sys
import argparse
from pprint import pprint

# Ensure Windows PowerShell/CMD terminal supports UTF-8 characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.graph.workflow import create_hedge_fund_graph

def run_investment_committee(ticker: str):
    ticker = ticker.upper().strip()
    print("\n" + "="*75)
    print(f"🏛️  AI HEDGE FUND: AUTONOMOUS INVESTMENT COMMITTEE")
    print(f"    Evaluating Target Asset: {ticker}")
    print("="*75)
    
    app = create_hedge_fund_graph()
    
    initial_state = {
        "ticker": ticker,
        "debate_round": 0,
        "debate_history": [],
        "bull_arguments": [],
        "bear_arguments": [],
        "logs": []
    }
    
    print("\n[+] Initializing Multi-Agent StateGraph...")
    final_state = app.invoke(initial_state)
    
    # Print Execution Logs
    print("\n[--- Committee Progress Logs ---]")
    for log in final_state.get("logs", []):
        print(f"  • {log}")
        
    tech = final_state["technical_analysis"]
    risk = final_state["risk_assessment"]
    order = final_state["final_order"]
    
    print("\n" + "-"*75)
    print(f"📊 1. QUANTITATIVE TECHNICAL SCREEN")
    print(f"   Current Price: ${tech['current_price']} ({tech['change_pct']}%)")
    print(f"   Trend: {tech['trend']} | RSI (14): {tech['rsi_14']} | SMA 50: ${tech['sma_50']}")
    print(f"   Annualized Volatility: {tech['annualized_volatility']*100:.1f}%")
    
    print("\n" + "-"*75)
    print(f"⚔️  2. ADVERSARIAL DEBATE TRANSCRIPT")
    bull_args = final_state["bull_arguments"]
    bear_args = final_state["bear_arguments"]
    
    for i in range(len(bull_args)):
        print(f"\n   [🥊 Debate Round {i+1}]")
        print(f"   🟢 Bull Strategist:\n      {bull_args[i]}")
        if i < len(bear_args):
            print(f"   🔴 Bear Skeptic:\n      {bear_args[i]}")
            
    print("\n" + "-"*75)
    print(f"🛡️  3. CHIEF RISK OFFICER (CRO) MANDATE")
    print(f"   Risk Rating: {risk['risk_rating']} | Veto Activated: {risk['is_vetoed']}")
    print(f"   Parametric 95% Daily VaR: {risk['var_95']}%")
    print(f"   Max Allocation Limit: {risk['max_position_size_pct']*100:.1f}%")
    print(f"   Risk Directive: {risk['risk_summary']}")
    
    print("\n" + "="*75)
    print(f"🎯 4. CHIEF INVESTMENT OFFICER (CIO) FINAL ALLOCATION ORDER")
    print(f"   RECOMMENDATION:     [{order['action']}]")
    print(f"   TARGET ALLOCATION:  {order['target_allocation_pct']*100:.1f}%")
    print(f"   CONVICTION SCORE:   {order['confidence']*100:.1f}%")
    if order.get("stop_loss_price"):
        print(f"   STOP LOSS PRICE:    ${order['stop_loss_price']}")
    if order.get("take_profit_price"):
        print(f"   TAKE PROFIT TARGET: ${order['take_profit_price']}")
    print(f"\n   EXECUTIVE THESIS:")
    print(f"   \"{order['executive_thesis']}\"")
    print("="*75 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AI Hedge Fund multi-agent committee on a stock.")
    parser.add_argument("--ticker", type=str, default="NVDA", help="Ticker symbol to analyze (e.g. NVDA, AAPL, MSFT)")
    args = parser.parse_args()
    
    run_investment_committee(args.ticker)
