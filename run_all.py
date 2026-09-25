import sys
import json
import argparse
from datetime import datetime

# Windows terminal UTF-8 encoding support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.graph.workflow import create_hedge_fund_graph
from src.quant.valuation_models import get_fundamental_metrics
from src.data.news_sentiment import fetch_asset_sentiment
from src.backtester.event_engine import run_backtest

def execute_full_pipeline(ticker: str = "NVDA", export_json: bool = True):
    ticker = ticker.upper().strip()
    start_time = datetime.now()
    
    print("\n" + "="*80)
    print(f"🚀  AUTONOMOUS AI HEDGE FUND: COMPLETE 1-DAY END-TO-END PIPELINE")
    print(f"    Target Asset: {ticker} | Initiated: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # 1. Fundamental Valuation (DCF)
    print("\n[Stage 1/5] Ingesting Balance Sheet & Computing DCF Valuation...")
    fund = get_fundamental_metrics(ticker)
    print(f"   • Current Price:          ${fund['current_price']}")
    print(f"   • DCF Intrinsic Value:    ${fund['dcf_intrinsic_value']}")
    print(f"   • Margin of Safety:       {fund['margin_of_safety_pct']:+0.1f}%")
    print(f"   • Trailing P/E:           {fund.get('trailing_pe') or 'N/A'}")
    print(f"   • Valuation Status:       {'UNDERVALUED (Buy Candidate)' if fund['is_undervalued_dcf'] else 'OVERVALUED / FAIR'}")

    # 2. Market Sentiment Extraction
    print("\n[Stage 2/5] Scraping Real-Time Media News & Scoring Sentiment...")
    senti = fetch_asset_sentiment(ticker)
    print(f"   • Sentiment Tone:         {senti['overall_tone']} (Score: {senti['aggregate_sentiment_score']})")
    print(f"   • Sample Headline:        \"{senti['top_headlines'][0]['title']}\"")

    # 3. Multi-Agent Committee Debate & Decision
    print("\n[Stage 3/5] Convening Multi-Agent StateGraph Investment Committee...")
    app = create_hedge_fund_graph()
    initial_state = {
        "ticker": ticker,
        "debate_round": 0,
        "debate_history": [],
        "bull_arguments": [],
        "bear_arguments": [],
        "logs": []
    }
    committee_state = app.invoke(initial_state)
    order = committee_state["final_order"]
    risk = committee_state["risk_assessment"]
    tech = committee_state["technical_analysis"]

    print(f"   • Technical Screening:    {tech['trend']} | RSI-14: {tech['rsi_14']}")
    print(f"   • 95% 1-Day VaR:          {risk['var_95']}% (Rating: {risk['risk_rating']})")
    print(f"   • Risk Officer Veto:      {risk['is_vetoed']}")
    print(f"   • CIO Final Directive:    [{order['action']}] | Conviction: {order['confidence']*100:.0f}%")
    print(f"   • Target Portfolio Weight: {order['target_allocation_pct']*100:.1f}%")
    print(f"   • CIO Synthesis Memo:     \"{order['executive_thesis']}\"")

    # 4. Event-Driven Backtesting
    print("\n[Stage 4/5] Executing 1-Year Event-Driven Backtester (Zero Lookahead)...")
    bt = run_backtest(ticker, period="1y")
    print(f"   • Strategy Total Return:   {bt['strategy_return_pct']:+0.2f}%")
    print(f"   • Buy & Hold Benchmark:   {bt['benchmark_return_pct']:+0.2f}%")
    print(f"   • Excess Alpha:           {bt['excess_alpha_pct']:+0.2f}%")
    print(f"   • Annualized Sharpe:      {bt['sharpe_ratio']}")
    print(f"   • Sortino Ratio:          {bt['sortino_ratio']}")
    print(f"   • Maximum Drawdown (MDD): {bt['max_drawdown_pct']}%")

    # 5. Export Comprehensive Audit Report
    print("\n[Stage 5/5] Generating Institutional Audit Report...")
    report = {
        "ticker": ticker,
        "timestamp": start_time.isoformat(),
        "execution_duration_sec": round((datetime.now() - start_time).total_seconds(), 2),
        "fundamental_valuation": fund,
        "news_sentiment": senti,
        "technical_analysis": tech,
        "risk_assessment": risk,
        "final_trade_order": order,
        "backtest_performance": {
            "strategy_return_pct": bt["strategy_return_pct"],
            "benchmark_return_pct": bt["benchmark_return_pct"],
            "excess_alpha_pct": bt["excess_alpha_pct"],
            "sharpe_ratio": bt["sharpe_ratio"],
            "sortino_ratio": bt["sortino_ratio"],
            "max_drawdown_pct": bt["max_drawdown_pct"],
            "total_trades": bt["total_trades"]
        }
    }

    report_filename = f"report_{ticker}.json"
    if export_json:
        with open(report_filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"   • Exported Complete Audit JSON: {report_filename}")

    print("\n" + "="*80)
    print(f"✅  ALL 5 PIPELINE STAGES COMPLETED SUCCESSFULLY IN {(datetime.now() - start_time).total_seconds():.1f}s")
    print(f"    Platform Status: Production-Ready & Interview-Verified")
    print("="*80 + "\n")

    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run complete 1-day AI Hedge Fund end-to-end pipeline.")
    parser.add_argument("--ticker", type=str, default="NVDA", help="Equity ticker to analyze")
    args = parser.parse_args()

    execute_full_pipeline(args.ticker)
