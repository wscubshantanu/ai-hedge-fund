"""AI agent report and debate models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey
from backend.app.database import Base


class AgentReport(Base):
    __tablename__ = "agent_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=True)
    ticker = Column(String, nullable=False, index=True)
    agent_name = Column(String, nullable=False)  # value_analyst, growth_analyst, etc.
    score = Column(Float, nullable=True)
    recommendation = Column(String)  # BUY, SELL, HOLD
    confidence = Column(Float)
    reasoning = Column(Text)
    evidence = Column(JSON)
    risks = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Debate(Base):
    __tablename__ = "debates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=True)
    ticker = Column(String, nullable=False, index=True)
    rounds_completed = Column(Integer, default=0)
    bull_arguments = Column(JSON)
    bear_arguments = Column(JSON)
    moderator_summary = Column(Text)
    consensus = Column(String)  # BULLISH, BEARISH, NEUTRAL
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class InvestmentDecision(Base):
    __tablename__ = "investment_decisions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    ticker = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # BUY, SELL, HOLD
    target_allocation_pct = Column(Float)
    confidence = Column(Float)
    stop_loss_price = Column(Float)
    take_profit_price = Column(Float)
    executive_thesis = Column(Text)
    bull_bear_consensus = Column(Text)
    fundamental_score = Column(Float)
    technical_score = Column(Float)
    sentiment_score = Column(Float)
    valuation_score = Column(Float)
    risk_rating = Column(String)
    guardrail_action = Column(String)  # APPROVED, MODIFIED, VETOED
    guardrail_notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
