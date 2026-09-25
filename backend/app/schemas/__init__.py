"""AETHER Capital — API Schemas (Pydantic v2)"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Auth Schemas ─────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, examples=["analyst@aether.fund"])
    username: str = Field(..., min_length=3, max_length=50, examples=["shantanu"])
    password: str = Field(..., min_length=6, examples=["quant2026"])
    full_name: Optional[str] = Field(None, examples=["Shantanu Kalhapure"])


class LoginRequest(BaseModel):
    email: str = Field(..., examples=["analyst@aether.fund"])
    password: str = Field(..., examples=["quant2026"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ── Analysis Schemas ─────────────────────────────────────────────
class AnalysisRequest(BaseModel):
    ticker: str = Field(default="NVDA", examples=["NVDA"])


class ScoreBreakdown(BaseModel):
    name: str
    value: float
    weight: float
    contribution: float
    description: str


class TechnicalResult(BaseModel):
    score: float = Field(ge=0, le=100)
    current_price: float
    trend: str
    indicators: Dict[str, Any]
    score_breakdown: List[ScoreBreakdown]
    data_source: str = "live"


class FundamentalResult(BaseModel):
    score: float = Field(ge=0, le=100)
    metrics: Dict[str, Any]
    strengths: List[str]
    weaknesses: List[str]
    score_breakdown: List[ScoreBreakdown]


class ValuationResult(BaseModel):
    score: float = Field(ge=0, le=100)
    dcf_value: float
    graham_number: Optional[float]
    gordon_growth_value: Optional[float]
    relative_valuation: Dict[str, Any]
    margin_of_safety_pct: float
    verdict: str


class SentimentResult(BaseModel):
    score: float = Field(ge=0, le=100)
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    overall_tone: str
    headlines: List[Dict[str, Any]]
    data_source: str


# ── Agent Schemas ────────────────────────────────────────────────
class AgentOpinion(BaseModel):
    agent_name: str
    score: float
    recommendation: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    key_evidence: List[str]
    key_risks: List[str]


class DebateResult(BaseModel):
    rounds: int
    bull_arguments: List[str]
    bear_arguments: List[str]
    moderator_summary: str
    consensus: str
    facts: List[str]
    assumptions: List[str]
    opinions: List[str]


class CIODecision(BaseModel):
    ticker: str
    action: str
    target_allocation_pct: float
    confidence: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    thesis: str
    key_risks: List[str]
    catalysts: List[str]
    invalidating_conditions: List[str]
    fundamental_score: float
    technical_score: float
    sentiment_score: float
    valuation_score: float


# ── Portfolio Schemas ────────────────────────────────────────────
class PortfolioOptimizeRequest(BaseModel):
    tickers: List[str] = Field(default=["NVDA", "AAPL", "MSFT", "GOOGL", "TSLA"])
    risk_free_rate: float = Field(default=0.04, ge=0.0, le=0.15)
    custom_views: Optional[Dict[str, float]] = None


class PositionResponse(BaseModel):
    ticker: str
    shares: float
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    weight_pct: float


class PortfolioResponse(BaseModel):
    cash: float
    equity_value: float
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    positions: List[PositionResponse]
    recent_trades: List[Dict[str, Any]]


# ── Trading Schemas ──────────────────────────────────────────────
class TradeOrderRequest(BaseModel):
    ticker: str = Field(..., examples=["NVDA"])
    side: str = Field(..., examples=["BUY"])  # BUY or SELL
    allocation_pct: Optional[float] = Field(None, ge=0.0, le=1.0, examples=[0.15])
    quantity: Optional[float] = Field(None, ge=0, examples=[10])
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class TradePreview(BaseModel):
    ticker: str
    side: str
    estimated_shares: float
    estimated_cost: float
    current_price: float
    guardrail_result: Dict[str, Any]
    risk_check: Dict[str, Any]


class TradeResult(BaseModel):
    status: str
    trade: Dict[str, Any]
    guardrails: Dict[str, Any]
    portfolio: PortfolioResponse


# ── Backtest Schemas ─────────────────────────────────────────────
class BacktestRequest(BaseModel):
    ticker: str = Field(default="NVDA", examples=["NVDA"])
    period: str = Field(default="1y", examples=["1y"])
    initial_capital: float = Field(default=100_000.0, ge=1000.0)
    rebalance_days: int = Field(default=5, ge=1, le=30)
    slippage_bps: float = Field(default=5.0, ge=0.0, le=50.0)


class BacktestResult(BaseModel):
    ticker: str
    period: str
    initial_capital: float
    final_capital: float
    strategy_return_pct: float
    benchmark_return_pct: float
    excess_alpha_pct: float
    cagr_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    profit_factor: float
    total_trades: int
    avg_trade_pnl: float
    equity_curve: List[float]
    benchmark_curve: List[float]
    dates: List[str]


# ── Monte Carlo Schemas ──────────────────────────────────────────
class MonteCarloRequest(BaseModel):
    ticker: str = Field(default="NVDA", examples=["NVDA"])
    forecast_days: int = Field(default=60, ge=10, le=252)
    simulations: int = Field(default=2000, ge=500, le=5000)


# ── Risk Schemas ─────────────────────────────────────────────────
class RiskCheckRequest(BaseModel):
    ticker: str
    allocation_pct: float = Field(ge=0.0, le=1.0)
    action: str = "BUY"


# ── Audit Schema ─────────────────────────────────────────────────
class AuditEntry(BaseModel):
    id: str
    event_type: str
    ticker: Optional[str]
    action: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True
