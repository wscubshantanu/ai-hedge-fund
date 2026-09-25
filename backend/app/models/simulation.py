"""Backtest and Monte Carlo simulation models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey
from backend.app.database import Base


class BacktestRun(Base):
    __tablename__ = "backtests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    ticker = Column(String, nullable=False, index=True)
    period = Column(String, nullable=False)
    strategy = Column(String, default="momentum_sma")
    initial_capital = Column(Float)
    final_capital = Column(Float)
    strategy_return_pct = Column(Float)
    benchmark_return_pct = Column(Float)
    excess_alpha_pct = Column(Float)
    cagr_pct = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    max_drawdown_pct = Column(Float)
    win_rate_pct = Column(Float)
    profit_factor = Column(Float)
    total_trades = Column(Integer)
    avg_trade_pnl = Column(Float)
    results = Column(JSON)  # Full results including equity curve
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class MonteCarloRun(Base):
    __tablename__ = "monte_carlo_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    ticker = Column(String, nullable=False, index=True)
    current_price = Column(Float)
    forecast_days = Column(Integer)
    num_simulations = Column(Integer)
    median_terminal = Column(Float)
    worst_case_p5 = Column(Float)
    best_case_p95 = Column(Float)
    probability_profit_pct = Column(Float)
    results = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
