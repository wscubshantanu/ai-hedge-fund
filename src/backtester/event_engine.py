import sys
import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, Any, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_backtest(
    ticker: str = "NVDA",
    period: str = "1y",
    initial_capital: float = 100_000.0,
    rebalance_frequency_days: int = 5,
    slippage_bps: float = 5.0  # 5 basis points = 0.05%
) -> Dict[str, Any]:
    """
    Event-driven simulation engine with strictly zero lookahead bias:
    - Steps chronologically across trading days
    - Rebalances every N days using only data known up to timestamp t
    - Models execution slippage and cash drag
    - Compares strategy equity curve against Buy-and-Hold benchmark
    """
    df = yf.Ticker(ticker).history(period=period)
    if df.empty or len(df) < 50:
        raise ValueError(f"Insufficient historical data for backtesting {ticker}")

    # Ensure no NaN values in Close series
    clean_series = df['Close'].ffill().bfill().dropna()
    closes = clean_series.values
    dates = [str(d.date()) for d in clean_series.index]
    n_days = len(closes)

    cash = initial_capital
    shares = 0.0
    portfolio_history: List[float] = []
    benchmark_history: List[float] = []
    trades: List[Dict[str, Any]] = []

    initial_price = float(closes[0])
    benchmark_shares = initial_capital / (initial_price if initial_price > 0 else 1.0)

    # Simulation loop
    for t in range(n_days):
        current_price = closes[t]
        port_val = cash + (shares * current_price)
        portfolio_history.append(port_val)
        benchmark_history.append(benchmark_shares * current_price)

        # Rebalancing decision on scheduled trading intervals
        if t >= 30 and (t % rebalance_frequency_days == 0):
            # Compute past indicators without lookahead (strictly 0:t)
            past_prices = closes[:t+1]
            sma_20 = np.mean(past_prices[-20:])
            sma_50 = np.mean(past_prices[-min(50, len(past_prices)):])
            
            # Simple momentum & trend following rule
            if current_price > sma_20 and sma_20 > sma_50:
                # Bullish signal -> Allocate up to 80% capital
                target_equity = port_val * 0.80
                target_shares = target_equity / current_price
                share_diff = target_shares - shares

                if share_diff > 0:
                    cost_per_share = current_price * (1.0 + (slippage_bps / 10000.0))
                    cost = share_diff * cost_per_share
                    if cash >= cost:
                        cash -= cost
                        shares += share_diff
                        trades.append({"date": dates[t], "action": "BUY", "shares": round(share_diff, 2), "price": round(current_price, 2)})
            elif current_price < sma_50:
                # Bearish breakdown -> Move to cash
                if shares > 0:
                    proceeds_per_share = current_price * (1.0 - (slippage_bps / 10000.0))
                    proceeds = shares * proceeds_per_share
                    cash += proceeds
                    trades.append({"date": dates[t], "action": "SELL", "shares": round(shares, 2), "price": round(current_price, 2)})
                    shares = 0.0

    final_portfolio_value = cash + (shares * closes[-1])
    strategy_return = ((final_portfolio_value - initial_capital) / initial_capital) * 100
    benchmark_return = ((benchmark_history[-1] - initial_capital) / initial_capital) * 100

    # Calculate returns series
    port_series = pd.Series(portfolio_history)
    daily_returns = port_series.pct_change().dropna()

    # Risk Metrics
    trading_days = 252
    risk_free_rate = 0.04
    mean_ret = daily_returns.mean() * trading_days
    std_ret = daily_returns.std() * np.sqrt(trading_days)
    sharpe_ratio = (mean_ret - risk_free_rate) / (std_ret + 1e-9)

    # Sortino Ratio (Downside deviation)
    downside_returns = daily_returns[daily_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(trading_days)
    sortino_ratio = (mean_ret - risk_free_rate) / (downside_std + 1e-9)

    # Maximum Drawdown (MDD)
    rolling_max = port_series.cummax()
    drawdowns = (port_series - rolling_max) / rolling_max
    max_drawdown = drawdowns.min() * 100

    return {
        "ticker": ticker,
        "period": period,
        "initial_capital": initial_capital,
        "final_capital": round(final_portfolio_value, 2),
        "strategy_return_pct": round(strategy_return, 2),
        "benchmark_return_pct": round(benchmark_return, 2),
        "excess_alpha_pct": round(strategy_return - benchmark_return, 2),
        "sharpe_ratio": round(float(sharpe_ratio), 2),
        "sortino_ratio": round(float(sortino_ratio), 2),
        "max_drawdown_pct": round(float(max_drawdown), 2),
        "total_trades": len(trades),
        "portfolio_history": [round(x, 2) for x in portfolio_history],
        "dates": dates
    }

if __name__ == "__main__":
    res = run_backtest("NVDA", period="1y")
    print("\n" + "="*60)
    print(f"📈 BACKTESTING RESULTS FOR {res['ticker']} (1-Year Horizon)")
    print("="*60)
    print(f"Initial Capital:         ${res['initial_capital']:,.2f}")
    print(f"Final Strategy Value:    ${res['final_capital']:,.2f}")
    print(f"Strategy Total Return:    {res['strategy_return_pct']}%")
    print(f"Buy & Hold Benchmark:    {res['benchmark_return_pct']}%")
    print(f"Excess Alpha Generated:   {res['excess_alpha_pct']}%")
    print(f"Sharpe Ratio:             {res['sharpe_ratio']}")
    print(f"Sortino Ratio:            {res['sortino_ratio']}")
    print(f"Max Drawdown:             {res['max_drawdown_pct']}%")
    print(f"Total Rebalances:         {res['total_trades']}")
    print("="*60 + "\n")
