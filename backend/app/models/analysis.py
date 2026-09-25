"""Analysis result models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey
from backend.app.database import Base


class Analysis(Base):
    """Master analysis record linking all sub-analyses for a ticker."""
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    overall_score = Column(Float, nullable=True)
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TechnicalAnalysis(Base):
    __tablename__ = "technical_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=True)
    ticker = Column(String, nullable=False, index=True)
    score = Column(Float, nullable=True)  # 0-100
    current_price = Column(Float)
    trend = Column(String)
    rsi = Column(Float)
    macd_signal_type = Column(String)  # BULLISH, BEARISH, NEUTRAL
    volatility = Column(Float)
    indicators = Column(JSON)  # Full indicator dict
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FundamentalAnalysis(Base):
    __tablename__ = "fundamental_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=True)
    ticker = Column(String, nullable=False, index=True)
    score = Column(Float, nullable=True)  # 0-100
    revenue_growth = Column(Float)
    eps_growth = Column(Float)
    gross_margin = Column(Float)
    operating_margin = Column(Float)
    roe = Column(Float)
    debt_to_equity = Column(Float)
    strengths = Column(JSON)
    weaknesses = Column(JSON)
    metrics = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ValuationAnalysis(Base):
    __tablename__ = "valuation_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=True)
    ticker = Column(String, nullable=False, index=True)
    score = Column(Float, nullable=True)  # 0-100
    dcf_value = Column(Float)
    graham_number = Column(Float)
    gordon_growth_value = Column(Float)
    relative_valuation = Column(JSON)
    margin_of_safety_pct = Column(Float)
    is_undervalued = Column(String)  # YES, NO, FAIR
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=True)
    ticker = Column(String, nullable=False, index=True)
    score = Column(Float, nullable=True)  # 0-100
    positive_pct = Column(Float)
    neutral_pct = Column(Float)
    negative_pct = Column(Float)
    overall_tone = Column(String)
    headlines = Column(JSON)
    data_source = Column(String, default="yahoo_finance")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
