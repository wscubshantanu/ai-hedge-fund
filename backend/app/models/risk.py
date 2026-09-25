"""Risk assessment model."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from backend.app.database import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=True)
    ticker = Column(String, nullable=False, index=True)
    is_vetoed = Column(Boolean, default=False)
    risk_rating = Column(String)  # LOW, MODERATE, HIGH, EXTREME
    var_95 = Column(Float)
    var_99 = Column(Float)
    cvar_95 = Column(Float)
    max_position_size_pct = Column(Float)
    portfolio_volatility = Column(Float)
    max_drawdown = Column(Float)
    concentration_risk = Column(Float)
    risk_summary = Column(Text)
    guardrail_decision = Column(String)  # APPROVED, MODIFIED, VETOED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
