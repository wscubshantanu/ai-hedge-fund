from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    ticker: str = Field(default="NVDA", example="NVDA")
    max_rounds: int = Field(default=2, ge=1, le=5)

class PortfolioOptimizationRequest(BaseModel):
    tickers: List[str] = Field(default=["NVDA", "AAPL", "MSFT", "GOOGL", "TSLA"], example=["NVDA", "AAPL", "MSFT"])
    risk_free_rate: float = Field(default=0.04, ge=0.0, le=0.15)
    custom_views: Optional[Dict[str, float]] = Field(default=None, example={"NVDA": 0.25})

class MonteCarloRequest(BaseModel):
    ticker: str = Field(default="NVDA", example="NVDA")
    forecast_days: int = Field(default=60, ge=10, le=252)
    simulations: int = Field(default=2000, ge=500, le=10000)

class BacktestRequest(BaseModel):
    ticker: str = Field(default="NVDA", example="NVDA")
    period: str = Field(default="1y", example="1y")
    initial_capital: float = Field(default=100000.0, ge=1000.0)
    rebalance_days: int = Field(default=5, ge=1, le=30)
    slippage_bps: float = Field(default=5.0, ge=0.0, le=50.0)

class TradeDecisionResponse(BaseModel):
    ticker: str
    action: str
    target_allocation_pct: float
    confidence: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    executive_thesis: str
    bull_bear_consensus: str

class FullAnalysisResponse(BaseModel):
    ticker: str
    status: str
    decision: TradeDecisionResponse
    risk_audit: Dict[str, Any]
    technicals: Dict[str, Any]
    fundamentals: Optional[Dict[str, Any]] = None
    debate_summary: Dict[str, Any]
