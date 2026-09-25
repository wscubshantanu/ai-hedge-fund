import numpy as np
from typing import Dict, Any, List

def run_monte_carlo_simulation(
    current_price: float,
    annual_volatility: float,
    drift_annual: float = 0.10,
    forecast_days: int = 60,
    num_simulations: int = 2000,
    stop_loss_pct: float = 0.08,
    take_profit_pct: float = 0.15
) -> Dict[str, Any]:
    """
    Simulates forward price distribution using Geometric Brownian Motion (GBM):
    dS_t = mu * S_t * dt + sigma * S_t * dW_t
    """
    dt = 1.0 / 252.0
    daily_drift = (drift_annual - 0.5 * (annual_volatility ** 2)) * dt
    daily_vol = annual_volatility * np.sqrt(dt)

    # Generate random standard normal shocks
    np.random.seed(42)
    random_shocks = np.random.normal(0, 1, (num_simulations, forecast_days))
    
    # Compute log returns and price paths
    log_returns = daily_drift + daily_vol * random_shocks
    cumulative_returns = np.cumsum(log_returns, axis=1)
    
    # Prepend starting price
    price_paths = np.zeros((num_simulations, forecast_days + 1))
    price_paths[:, 0] = current_price
    price_paths[:, 1:] = current_price * np.exp(cumulative_returns)

    # Key Quant Stats across simulated paths
    terminal_prices = price_paths[:, -1]
    median_terminal = float(np.median(terminal_prices))
    p5_terminal = float(np.percentile(terminal_prices, 5))    # 95% worst-case
    p25_terminal = float(np.percentile(terminal_prices, 25))
    p75_terminal = float(np.percentile(terminal_prices, 75))
    p95_terminal = float(np.percentile(terminal_prices, 95))   # 95% best-case

    prob_profit = float(np.mean(terminal_prices > current_price) * 100)

    # Path-dependent barrier hits (Stop-loss vs Take-profit)
    stop_price = current_price * (1.0 - stop_loss_pct)
    take_price = current_price * (1.0 + take_profit_pct)

    hit_stop = np.any(price_paths <= stop_price, axis=1)
    hit_take = np.any(price_paths >= take_price, axis=1)

    prob_hit_stop = float(np.mean(hit_stop) * 100)
    prob_hit_take = float(np.mean(hit_take) * 100)

    # Fan chart percentiles for visualization
    days = list(range(forecast_days + 1))
    median_path = [round(float(x), 2) for x in np.median(price_paths, axis=0)]
    upper_95_path = [round(float(x), 2) for x in np.percentile(price_paths, 95, axis=0)]
    lower_5_path = [round(float(x), 2) for x in np.percentile(price_paths, 5, axis=0)]
    upper_75_path = [round(float(x), 2) for x in np.percentile(price_paths, 75, axis=0)]
    lower_25_path = [round(float(x), 2) for x in np.percentile(price_paths, 25, axis=0)]

    return {
        "current_price": round(current_price, 2),
        "forecast_horizon_days": forecast_days,
        "num_simulations": num_simulations,
        "median_terminal_price": round(median_terminal, 2),
        "worst_case_p5": round(p5_terminal, 2),
        "best_case_p95": round(p95_terminal, 2),
        "expected_return_pct": round(((median_terminal - current_price) / current_price) * 100, 2),
        "probability_of_profit_pct": round(prob_profit, 1),
        "probability_hit_stop_loss": round(prob_hit_stop, 1),
        "probability_hit_take_profit": round(prob_hit_take, 1),
        "fan_chart": {
            "days": days,
            "median": median_path,
            "upper_95": upper_95_path,
            "lower_5": lower_5_path,
            "upper_75": upper_75_path,
            "lower_25": lower_25_path
        }
    }
