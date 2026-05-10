from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Candle(Base):
    __tablename__ = "candles"
    __table_args__ = (UniqueConstraint("market", "timeframe", "candle_time_kst", name="uq_candle"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market: Mapped[str] = mapped_column(String(32), index=True)
    timeframe: Mapped[str] = mapped_column(String(16), index=True)
    candle_time_kst: Mapped[str] = mapped_column(String(32), index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    trade_price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Tick(Base):
    __tablename__ = "ticks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market: Mapped[str] = mapped_column(String(32), index=True)
    tick_type: Mapped[str] = mapped_column(String(32), index=True)
    event_time_kst: Mapped[str] = mapped_column(String(32), index=True)
    trade_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    trade_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    ask_bid: Mapped[str | None] = mapped_column(String(8), nullable=True)
    orderbook_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PersonaScore(Base):
    __tablename__ = "persona_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    market: Mapped[str] = mapped_column(String(32), index=True)
    persona_name: Mapped[str] = mapped_column(String(32))
    score: Mapped[float] = mapped_column(Float)
    decision: Mapped[str] = mapped_column(String(16))
    reasons_json: Mapped[str] = mapped_column(Text)
    warnings_json: Mapped[str] = mapped_column(Text)
    veto: Mapped[bool] = mapped_column(Boolean, default=False)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market: Mapped[str] = mapped_column(String(32), index=True)
    final_score: Mapped[float] = mapped_column(Float)
    final_decision: Mapped[str] = mapped_column(String(16))
    vetoed: Mapped[bool] = mapped_column(Boolean, default=False)
    veto_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    top_reasons_json: Mapped[str] = mapped_column(Text)
    config_version: Mapped[str] = mapped_column(String(32), default="v0.1")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OrderIntentRow(Base):
    __tablename__ = "order_intents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("signals.id"), nullable=True)
    market: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    ord_type: Mapped[str] = mapped_column(String(16))
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    krw_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    identifier: Mapped[str] = mapped_column(String(128), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="CREATED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OrderTestResult(Base):
    __tablename__ = "order_test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_intent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    market: Mapped[str] = mapped_column(String(32), index=True)
    request_json: Mapped[str] = mapped_column(Text)
    response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PaperPosition(Base):
    __tablename__ = "paper_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market: Mapped[str] = mapped_column(String(32), index=True)
    avg_price: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    invested_krw: Mapped[float] = mapped_column(Float)
    unrealized_pnl_krw: Mapped[float] = mapped_column(Float, default=0)
    unrealized_pnl_pct: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(16), default="OPEN")
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PaperTrade(Base):
    __tablename__ = "paper_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("paper_positions.id"), nullable=True)
    market: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    price: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    fee_krw: Mapped[float] = mapped_column(Float)
    slippage_krw: Mapped[float] = mapped_column(Float)
    realized_pnl_krw: Mapped[float] = mapped_column(Float, default=0)
    realized_pnl_pct: Mapped[float] = mapped_column(Float, default=0)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_date: Mapped[str] = mapped_column(String(16), index=True)
    signal_count: Mapped[int] = mapped_column(Integer)
    entered_count: Mapped[int] = mapped_column(Integer)
    win_count: Mapped[int] = mapped_column(Integer)
    loss_count: Mapped[int] = mapped_column(Integer)
    realized_pnl_krw: Mapped[float] = mapped_column(Float)
    realized_pnl_pct: Mapped[float] = mapped_column(Float)
    max_drawdown_pct: Mapped[float] = mapped_column(Float)
    veto_count: Mapped[int] = mapped_column(Integer)
    markdown_path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConfigVersion(Base):
    __tablename__ = "config_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(32))
    persona_weights_json: Mapped[str] = mapped_column(Text)
    risk_json: Mapped[str] = mapped_column(Text)
    strategy_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

