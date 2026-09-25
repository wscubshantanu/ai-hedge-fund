from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AnalystSignal(BaseModel):
    agent_name: str = Field(description="Name of the analyst agent")
    signal: str = Field(description="BULLISH, BEARISH, or NEUTRAL")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    key_points: List[str] = Field(description="Key bullet points supporting the signal")
    metrics_summary: str = Field(description="Summary of core quantitative metrics")

class RiskEvaluation(BaseModel):
    is_vetoed: bool = Field(description="True if the trade violates risk boundaries")
    max_position_size_pct: float = Field(ge=0.0, le=1.0, description="Suggested allocation cap")
    var_95: float = Field(description="95% 1-Day Value-at-Risk percentage")
    risk_rating: str = Field(description="LOW, MODERATE, HIGH, or EXTREME")
    risk_summary: str = Field(description="Risk assessment commentary")

class FinalTradeOrder(BaseModel):
    ticker: str
    action: str = Field(description="BUY, SELL, or HOLD")
    target_allocation_pct: float = Field(ge=0.0, le=1.0, description="Portfolio allocation weight")
    confidence: float = Field(ge=0.0, le=1.0, description="CIO conviction score")
    stop_loss_price: Optional[float] = Field(default=None, description="Stop loss risk threshold")
    take_profit_price: Optional[float] = Field(default=None, description="Take profit target")
    executive_thesis: str = Field(description="Comprehensive CIO synthesis memo")
    bull_bear_consensus: str = Field(description="Summary of debate resolution")

class AgentState(TypedDict):
    ticker: str
    market_data: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    fundamental_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    bull_arguments: List[str]
    bear_arguments: List[str]
    debate_history: List[Dict[str, str]]
    debate_round: int
    risk_assessment: Optional[Dict[str, Any]]
    final_order: Optional[Dict[str, Any]]
    logs: List[str]
