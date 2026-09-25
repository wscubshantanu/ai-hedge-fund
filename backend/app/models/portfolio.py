"""Portfolio, position, order, and trade models."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey, Boolean
from backend.app.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, default="Default Portfolio")
    initial_cash = Column(Float, default=100_000.0)
    cash = Column(Float, default=100_000.0)
    realized_pnl = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Position(Base):
    __tablename__ = "positions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False, index=True)
    ticker = Column(String, nullable=False, index=True)
    shares = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    opened_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False, index=True)
    ticker = Column(String, nullable=False)
    side = Column(String, nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    order_type = Column(String, default="MARKET")
    status = Column(String, default="PENDING")  # PENDING, FILLED, REJECTED, CANCELLED
    limit_price = Column(Float, nullable=True)
    fill_price = Column(Float, nullable=True)
    guardrail_result = Column(String, nullable=True)
    guardrail_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    filled_at = Column(DateTime, nullable=True)


class Trade(Base):
    __tablename__ = "trades"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, ForeignKey("orders.id"), nullable=True)
    portfolio_id = Column(String, ForeignKey("portfolios.id"), nullable=False, index=True)
    ticker = Column(String, nullable=False, index=True)
    side = Column(String, nullable=False)
    shares = Column(Float, nullable=False)
    fill_price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    realized_pnl = Column(Float, nullable=True)
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
