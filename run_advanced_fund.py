import sys
import argparse
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.quant.portfolio_optimizer import optimize_portfolio_markowitz, black_litterman_allocation
from src.quant.monte_carlo import run_monte_carlo_simulation
from src.quant.valuation_models import get_fundamental_metrics
from src.quant.technical_indicators import get_market_technicals
from src.quant.regime_detector import detect_market_regime
from src.agents.personas import warren_buffett_analysis, cathie_wood_analysis, benjamin_graham_analysis, jim_simons_quant_analysis
import yfinance as yf

def execute_advanced_hedge_fund(tickers=None):
    if tickers is None or len(tickers) == 0:
        tickers = ["NVDA", "AAPL", "MSFT", "GOOGL", "TSLA"]
    tickers = [t.upper().strip() for t in tickers]

    print("\n" + "="*85)
    print("🏛️  ADVANCED MULTI-ASSET AI HEDGE FUND: INSTITUTIONAL PORTFOLIO MANAGEMENT")
    print(f"    Asset Universe: {', '.join(tickers)} | Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*85)

    # 1. Macro Regime Detection
    print("\n[Stage 1/5] Macroeconomic Volatility & Market Regime Detection...")
    spy_df = yf.Ticker("SPY").history(period="6mo")
    regime_data = detect_market_regime(spy_df)
    print(f"   • Active Market Regime:   {regime_data['regime']} (Confidence: {regime_data['confidence']*100:.0f}%)")
    print(f"   • S&P 500 Realized Vol:   {regime_data['annualized_volatility']}%")
    print(f"   • Capital Directive:      {regime_data['action_guidance']}")

    # 2. Multi-Persona Dialectic Committee
    print("\n[Stage 2/5] Convening Iconic Investor Persona Committee...")
    lead_ticker = tickers[0]
    lead_funds = get_fundamental_metrics(lead_ticker)
    lead_tech = get_market_technicals(lead_ticker)

    print(f"   Target Asset Spotlight: {lead_ticker} (${lead_tech['current_price']})")
    print(f"   • 👴 {warren_buffett_analysis(lead_ticker, lead_funds, lead_tech)}")
    print(f"   • 🚀 {cathie_wood_analysis(lead_ticker, lead_tech)}")
    print(f"   • ⚖️ {benjamin_graham_analysis(lead_ticker, lead_funds)}")
    print(f"   • 🧮 {jim_simons_quant_analysis(lead_ticker, lead_tech)}")

    # 3. Markowitz & Black-Litterman Portfolio Optimization
    print("\n[Stage 3/5] Modern Portfolio Theory (MPT) & Black-Litterman Allocation...")
    mpt = optimize_portfolio_markowitz(tickers)
    
    agent_views = {t: 0.18 if t in ["NVDA", "MSFT"] else 0.10 for t in tickers}
    agent_conf = {t: 0.85 if t in ["NVDA", "MSFT"] else 0.60 for t in tickers}
    bl = black_litterman_allocation(tickers, agent_views, agent_conf)

    print(f"   • Expected Portfolio Return:    {mpt['expected_annual_return']}%")
    print(f"   • Expected Portfolio Volatility:{mpt['expected_annual_volatility']}%")
    print(f"   • Max Sharpe Ratio:             {mpt['max_sharpe_ratio']}")
    print("\n   [Optimal Capital Allocations]")
    for t in mpt['tickers']:
        mpt_w = mpt['max_sharpe_weights'].get(t, 0.0) * 100
        bl_w = bl['black_litterman_weights'].get(t, 0.0) * 100
        print(f"      • {t:6s} | Markowitz Max Sharpe: {mpt_w:5.1f}% | Black-Litterman Blended: {bl_w:5.1f}%")

    # 4. Monte Carlo Forward Price Simulation (GBM)
    print(f"\n[Stage 4/5] 2,000-Path Monte Carlo Stochastic Risk Simulation ({lead_ticker})...")
    mc = run_monte_carlo_simulation(
        current_price=lead_tech['current_price'],
        annual_volatility=lead_tech['annualized_volatility'],
        forecast_days=60,
        num_simulations=2000
    )
    print(f"   • 60-Day Median Price:         ${mc['median_terminal_price']} (Expected Return: {mc['expected_return_pct']:+0.1f}%)")
    print(f"   • 95% Worst-Case Downside:     ${mc['worst_case_p5']}")
    print(f"   • 95% Best-Case Upside:        ${mc['best_case_p95']}")
    print(f"   • Probability of Profit:       {mc['probability_of_profit_pct']}%")
    print(f"   • Probability Hit Stop-Loss:   {mc['probability_hit_stop_loss']}%")

    # 5. Executive Synthesis
    print("\n" + "="*85)
    print("🎯 STAGE 5: CHIEF INVESTMENT OFFICER (CIO) PORTFOLIO MANDATE")
    print(f"   Strategic Posture: {regime_data['regime']} ACTIVE REBALANCING")
    print(f"   Top Capital Allocation: {max(bl['black_litterman_weights'], key=bl['black_litterman_weights'].get)} ({max(bl['black_litterman_weights'].values())*100:.1f}%)")
    print("="*85 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run advanced institutional multi-asset AI hedge fund.")
    parser.add_argument("--tickers", nargs="+", default=["NVDA", "AAPL", "MSFT", "GOOGL", "TSLA"], help="Universe of tickers")
    args = parser.parse_args()

    execute_advanced_hedge_fund(args.tickers)
